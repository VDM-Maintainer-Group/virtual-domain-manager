#![allow(dead_code)]

extern crate nix;
extern crate libc;
extern crate libloading;

use bimap::BiMap;
use rand::{Rng, thread_rng, distributions::Alphanumeric};
use std::path::Path;
use std::collections::HashMap;
use threadpool::ThreadPool;
//
use libc::{c_char};
use std::ffi::{CStr, CString, OsStr};
use pyo3::prelude::*;
use serde_json::{self, Value};
//
use crate::shared_consts::VDM_CAPABILITY_DIR;

type PyFuncName = String;
type PyLibCode = String;

// #[repr(u8)]
enum RawFunc<'a,T,R>
{
    Value0(libloading::Symbol<'a, extern fn()->R>),
    Value1(libloading::Symbol<'a, extern fn(T)->R>),
    Value2(libloading::Symbol<'a, extern fn(T,T)->R>),
    Value3(libloading::Symbol<'a, extern fn(T,T,T)->R>),
    Value4(libloading::Symbol<'a, extern fn(T,T,T,T)->R>),
    Value5(libloading::Symbol<'a, extern fn(T,T,T,T,T)->R>)
}

impl<'a,T,R> RawFunc<'a,T,R> {
    pub fn load<'lib>(lib:&'lib libloading::Library, name:&[u8], len:usize) -> Option<RawFunc<'lib,T,R>> {
        match len {
            0 => {
                if let Ok(sym) = unsafe{ lib.get(name) } {
                    Some(RawFunc::Value0(sym))
                } else {None}
            },
            1 => {
                if let Ok(sym) = unsafe{ lib.get(name) } {
                    Some(RawFunc::Value1(sym))
                } else {None}
            },
            2 => {
                if let Ok(sym) = unsafe{ lib.get(name) } {
                    Some(RawFunc::Value2(sym))
                } else {None}
            },
            3 => {
                if let Ok(sym) = unsafe{ lib.get(name) } {
                    Some(RawFunc::Value3(sym))
                } else {None}
            },
            4 => {
                if let Ok(sym) = unsafe{ lib.get(name) } {
                    Some(RawFunc::Value4(sym))
                } else {None}
            },
            5 => {
                if let Ok(sym) = unsafe{ lib.get(name) } {
                    Some(RawFunc::Value5(sym))
                } else {None}
            },
            _ => {None}
        }
    }

    pub fn call(&self, mut args:Vec<T>) -> Result<R, Box<dyn std::error::Error>>{
        let mut iter = args.drain(..);
        match self {
            Self::Value0(func) => {
                Ok(
                    func()
                )
            },
            Self::Value1(func) => {
                Ok(
                    func( iter.next().unwrap() )
                )
            },
            Self::Value2(func) => {
                Ok(
                    func( iter.next().unwrap(), iter.next().unwrap() )
                )
            },
            Self::Value3(func) => {
                Ok(
                    func( iter.next().unwrap(), iter.next().unwrap(), iter.next().unwrap() )
                )
            },
            Self::Value4(func) => {
                Ok(
                    func( iter.next().unwrap(), iter.next().unwrap(), iter.next().unwrap(),
                          iter.next().unwrap(), )
                )
            },
            Self::Value5(func) => {
                Ok(
                    func( iter.next().unwrap(), iter.next().unwrap(), iter.next().unwrap(),
                          iter.next().unwrap(), iter.next().unwrap(), )
                )
            }
        }
    }
}

enum Func<'a> {
    CFunc(RawFunc<'a,*const c_char, *const c_char>),
    RustFunc(RawFunc<'a,String, String>),
    PythonFunc((&'a PyLibCode, PyFuncName))
}

impl<'a> Func<'a> {
    pub fn new<'lib>(lib:&'lib LibraryContext, name:&String, len:usize) -> Option<Func<'lib>> {
        match lib {
            LibraryContext::CDLL(lib) => {
                if let Some(func) = RawFunc::load(lib, name.as_bytes(), len) {
                    Some( Func::CFunc(func) )
                } else {None}
            },
            LibraryContext::Rust(lib) => {
                if let Some(func) = RawFunc::load(lib, name.as_bytes(), len) {
                    Some( Func::RustFunc(func) )
                } else {None}
            }
            LibraryContext::Python(lib) => {
                Some( Func::PythonFunc((&lib, name.clone())) )
            }
        }
    }

    pub fn call(&self, args:Vec<Value>) -> String {
        let args: Vec<&Value> = args.iter().map(|arg| {
            let obj = arg.as_object().unwrap();
            let val = obj.values().next().unwrap();
            val
        }).collect();

        match self {
            Self::CFunc(func) => {
                let args:Vec<CString> = args.iter().map(|arg|{
                    CString::new( arg.to_string() ).unwrap()
                }).collect();
                let _args:Vec<*const c_char> = args.iter().map( |arg| {arg.as_ptr()} ).collect();
                unsafe{
                    CStr::from_ptr( func.call(_args).unwrap() ).to_string_lossy().into_owned()
                }
            },
            Self::RustFunc(func) => {
                let args:Vec<String> = args.iter().map(|arg|{
                    serde_json::to_string(arg).unwrap()
                }).collect();
                match func.call(args) {
                    Ok(res) => res,
                    Err(_) => String::new()   
                }
            },
            Self::PythonFunc(func) => {
                let (lib, func) = func;
                let args:Vec<String> = args.iter().map(|arg|{
                    serde_json::to_string(arg).unwrap()
                }).collect();

                let mut res = String::new();
                Python::with_gil(|py| {
                    if let Ok(module) = PyModule::from_code(py, lib, "__internal__.py", "__internal__") {
                        res = match args.len() {
                            0 => {
                                let args = ();
                                module.call1(func, args).unwrap().extract().unwrap()
                            }
                            1 => {
                                let args = (&args[0], );
                                module.call1(func, args).unwrap().extract().unwrap()
                            },
                            2 => {
                                let args = (&args[0], &args[1]);
                                module.call1(func, args).unwrap().extract().unwrap()
                            },
                            3 => {
                                let args = (&args[0], &args[1], &args[2]);
                                module.call1(func, args).unwrap().extract().unwrap()
                            },
                            4 => {
                                let args = (&args[0], &args[1], &args[2], &args[3]);
                                module.call1(func, args).unwrap().extract().unwrap()
                            },
                            5 => {
                                let args = (&args[0], &args[1], &args[2], &args[3], &args[4]);
                                module.call1(func, args).unwrap().extract().unwrap()
                            },
                            _ => { String::new() }
                        };
                    }
                });
                res
            }
        }
    }
}

enum LibraryContext {
    CDLL(libloading::Library),
    Rust(libloading::Library),
    Python(PyLibCode)
}

struct Library<'a> { //'a is lifetime of context
    context: LibraryContext,
    functions: HashMap<String, Func<'a>>
}

impl<'a> Library<'a> {
    pub fn new(_type:&str, entry:&Path) -> Option<Library<'a>> {
        let context = match _type {
            "c" | "cpp" => {
                if let Ok(lib) = unsafe{ libloading::Library::new(entry) } {
                    Some(LibraryContext::CDLL(lib))
                } else { None }
            },
            "rust" => {
                if let Ok(lib) = unsafe{ libloading::Library::new(entry) } {
                    Some(LibraryContext::Rust(lib))
                } else { None }
            }
            "python" => {
                if let Ok(contents) = std::fs::read_to_string(entry) {
                    Some(LibraryContext::Python(contents))
                } else { None }
            },
            _ => { None }
        };
        if let Some(context) = context {
            Some(Library{context, functions:HashMap::new()})
        } else {None}
    }

    pub fn load(&'a mut self, metadata:&Value) {
        for (key,val) in metadata.as_object().unwrap().iter() {
            let _args = &val.as_object().unwrap()["args"];
            let _len = _args.as_array().unwrap().len();
            if let Some(func) = Func::new(&self.context, &key, _len) {
                self.functions.insert(key.clone(), func);
            }
        }
    }
}

pub struct FFIManager<'a> {
    root: String,
    pool: ThreadPool,
    sig_name_map: BiMap<String, String>, //<sig, name>
    library: HashMap<String, (u32, Library<'a>)> //<name, (counter, _)>
}

// - On-demand load cdll library with "usage count"
//      - load from "~/.vdm/capability" using "ffi.rs"
//      - with "register" command, +1; with "unregister" command, -1
//      - zero for release
impl<'a> FFIManager<'a> {
    pub fn new() -> FFIManager<'a> {
        let _new = FFIManager{
            root: shellexpand::tilde(VDM_CAPABILITY_DIR).into_owned(),
            pool: ThreadPool::new(num_cpus::get()),
            sig_name_map: BiMap::new(),
            library: HashMap::new()
        };
        // switch to execution context when creation
        let libs_folder = Path::new(&_new.root).join("libs");
        nix::unistd::chdir( libs_folder.as_path() ).unwrap();
        _new
    }

    fn gen_sig() -> String {
        thread_rng().sample_iter(&Alphanumeric).take(16)
        .map(char::from).collect()
    }

    fn load(&mut self, manifest:&Value) -> Option<String> {
        let manifest = manifest.as_object().unwrap();
        let (name, entry, _type, metadata): (&str,&str,&str,&Value) = (
            manifest["name"].as_str().unwrap(),
            manifest["build"]["output"][0].as_str().unwrap(),
            manifest["type"].as_str().unwrap(),
            &manifest["metadata"]
        );

        let entry:Vec<&str> = entry.split('@').collect();
        let entry = match entry.len() {
            1 => Some( Path::new(entry[0]).file_name().unwrap() ),
            2 => Some( OsStr::new(entry[1]) ),
            _ => None
        };
        if let Some(entry) = entry {
            if let Some(mut lib) = Library::new(_type, entry.as_ref()) {
                lib.load(metadata);
                self.library.insert(
                    String::from(name),
                    (0, lib)
                );
            }
        }

        unimplemented!();
    }

    fn preload(&mut self) {
        unimplemented!();
    }

    pub fn register(&mut self, name: &str) -> Option<String> {
        let mut res = None;
        let manifest = Path::new(&self.root).join(name).join("manifest.json");

        if self.library.contains_key(name) {
            if let Some(sig) = self.sig_name_map.get_by_right(name) {
                res = Some( sig.clone() );
            }
        }
        else if manifest.exists() {
            let file = std::fs::File::open(manifest).unwrap();
            let reader = std::io::BufReader::new(file);
            let manifest:Value = serde_json::from_reader(reader).unwrap();
            if let Some(sig) = self.load(&manifest) {
                res = Some(sig);
            }
        }
        return res;
    }

    pub fn unregister(&mut self, name: &str) {
        unimplemented!();
    }

    pub fn execute<T>(&self, raw_data:String, callback:T)
    where T: FnOnce(String) -> ()
    {
        let v: Value = serde_json::from_slice(raw_data.as_bytes()).unwrap();
        self.pool.execute(move || {
            let sig  = v["sig"].as_str().unwrap();
            let func = v["func"].as_str().unwrap();
            let ref args:Value = v["args"];
            unimplemented!();
        });
    }

    pub fn chain_execute<T>(&self, raw_data:String, callback:T)
    where T: FnOnce(String) -> ()
    {
        let v: Value = serde_json::from_slice(raw_data.as_bytes()).unwrap();
        self.pool.execute(move || {
            let ref sig_func_args_table:Value = v["sig_func_args_table"];
            unimplemented!();
        });
    }
}
