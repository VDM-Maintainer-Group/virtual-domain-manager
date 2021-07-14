extern crate nix;
extern crate libc;
extern crate libloading;

use std::pin::Pin;
use bimap::BiMap;
use rand::{thread_rng, distributions::Alphanumeric};
use std::path::Path;
use threadpool::ThreadPool;
//
use libc::{c_char};
use std::ffi::{CStr, CString, OsStr};
use pyo3::prelude::*;
use serde_json::{self, Value};

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
    pub fn load<'lib>(lib:&'lib libloading::Library, name:&[u8], argc:usize) -> Option<RawFunc<'lib,T,R>> {
        match argc {
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
    pub fn new<'lib>(lib:&'lib LibraryContext, name:&String, argc:usize) -> Option<Func<'lib>> {
        match lib {
            LibraryContext::CDLL(lib) => {
                if let Some(func) = RawFunc::load(lib, name.as_bytes(), argc) {
                    Some( Func::CFunc(func) )
                } else {None}
            },
            LibraryContext::Rust(lib) => {
                if let Some(func) = RawFunc::load(lib, name.as_bytes(), argc) {
                    Some( Func::RustFunc(func) )
                } else {None}
            }
            LibraryContext::Python(lib) => {
                Some( Func::PythonFunc(( &lib, name.clone() )) )
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
    pub fn new(_type:&str, entry:&Path) -> Option<Pin<Box<Self>>> {
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
            let _lib = Library {context, functions:HashMap::new()};
            Some( Box::pin(_lib) )
        } else {None}
    }

    pub fn load(mut self, metadata:&Value) -> Self {
        for (key,val) in metadata.as_object().unwrap().iter() {
            let _args = &val.as_object().unwrap()["args"];
            let _len = _args.as_array().unwrap().len();
            //
            if let Some(func) = Func::new(&self.context, &key, _len) {
                unsafe {
                    // self.functions.insert(key.clone(), func);
                }
            }
        }
        self
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
            root: shellexpand::tilde("~/.vdm").into_owned(),
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
            if let Some(mut lib) = Library::new(_type, entry.as_ref()) { //FIXME: remove self-referential struct
                //reference: https://doc.rust-lang.org/nightly/std/pin/index.html#example-self-referential-struct
                // let _lib = lib.as_mut().load(metadata);
                // // lib = lib.as_mut().load(metadata);
                // self.library.insert(
                //     String::from(name),
                //     (0, _lib)
                // );
            }
            
            Some( String::new() )
        } else { None }
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


//======================================================================//
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::collections::{HashMap, BTreeMap, BTreeSet};
//
use rand::{self, Rng};
use serde::{Serialize,Deserialize};
use confy;
//
use crate::core::traits::Serde;
use crate::core::command::*;

pub type ArcFFIManagerStub = Arc<Mutex<FFIManagerStub>>;
pub type FFIDescriptor = (String, String, Vec<String>);

#[derive(Serialize, Deserialize)]
pub struct BuildTemplate {
    dependency: DepMap,
    script: Vec<String>,
    output: Vec<String>
}

#[derive(Serialize, Deserialize)]
pub struct RuntimeTemplate {
    dependency: DepMap,
    status: String,
    enable: Vec<String>,
    disable: Vec<String>
}

#[derive(Serialize, Deserialize)]
pub struct MetaFunc {
    name: String,
    restype: String,
    args: Vec<HashMap<String, String>>
}

#[derive(Serialize, Deserialize)]
pub struct Metadata {
    name: String,
    class: String,
    version: String,
    func: Vec<MetaFunc>
}

#[derive(Serialize, Deserialize)]
struct ServiceConfig {
    entry: String,
    files: Vec<String>,
    metadata: Option<Metadata>,
    runtime: Option<RuntimeTemplate>
}

impl Default for ServiceConfig {
    fn default() -> Self {
        Self{
            entry: String::new(), files: Vec::new(),
            metadata: None, runtime: None
        }
    }
}

type ServiceMap = BTreeMap<String, u32>;
type UsageMap   = BTreeMap<u32, BTreeSet<u32>>;

#[derive(Clone)]
pub struct FFIManagerStub {
    root: PathBuf,
    service_map: ServiceMap,
    usage_map: UsageMap
}

// internal basic functions
impl FFIManagerStub {
    pub fn new(root: PathBuf) -> Self {
        let service_map = BTreeMap::new();
        let usage_map   = BTreeMap::new();
        std::env::set_current_dir(&root).unwrap(); //panic as you like
        FFIManagerStub{ root, service_map, usage_map }
    }

    fn write_config_file(&self, cfg: ServiceConfig) -> ExecResult {
        let name = {
            if let Some(ref metadata) = cfg.metadata {
                PathBuf::from(&metadata.name)
            } else { PathBuf::new() }
        };
        let service_path:PathBuf =
                [&self.root, &name].iter().collect();
        std::fs::create_dir_all(&service_path).unwrap_or(());
        match confy::store_path(&service_path, cfg) {
            Ok(_) => Ok(()),
            Err(_) => Err( format!("Config file store failed for service '{}'.", name.display()) )
        }
    }

    fn load_config_file(&self, name:&String) -> Option<ServiceConfig> {
        let name = PathBuf::from(name);
        let service_path:PathBuf =
                [&self.root, &name].iter().collect();
        match confy::load_path(&service_path) {
            Ok(cfg) => Some(cfg),
            Err(_) => None
        }
    }

    fn prepare_runtime(&self, files:Vec<String>, metadata:Metadata, runtime:RuntimeTemplate) -> ExecResult
    {
        let commander = Commander::new(self.root.clone(), self.root.clone());
        commander.runtime_dependency( runtime.dependency.clone() )?;
        //
        let cfg = ServiceConfig{
            entry: String::from(&files[0]), files,
            metadata:Some(metadata), runtime:Some(runtime)
        };
        self.write_config_file(cfg)?;
        Ok(())
    }
}

// internal load/unload functions
impl FFIManagerStub {
    fn gen_sig() -> u32 {
        // thread_rng().sample_iter(&Alphanumeric).take(16).map(char::from).collect()
        rand::thread_rng().gen()
    }

    fn insert_service_map(&mut self, name: &String) -> Option<u32> {
        let service_sig = loop { //dead loop
            let sig = Self::gen_sig();
            if !self.usage_map.contains_key(&sig) {
                break sig
            }
        };

        self.service_map.insert( name.into(), service_sig )?;
        Some( service_sig )
    }

    fn insert_usage_map(&mut self, service_sig: &u32) -> Option<u32> {
        let usage_set = self.usage_map.get_mut(service_sig)?;
        let usage_sig = loop { //dead loop
            let sig = Self::gen_sig();
            if !usage_set.contains(&sig) {
                break sig
            }
        };

        usage_set.insert( usage_sig );
        Some( usage_sig )
    }

    fn load_service(&mut self, cfg: ServiceConfig) -> Option<()> {
        Some(())
    }
}

// service install / uninstall
impl FFIManagerStub {
    pub fn install(&self, directory:PathBuf, 
        metadata:Metadata, build:BuildTemplate, runtime:RuntimeTemplate) -> ExecResult 
    {
        let commander = Commander::new(self.root.clone(), directory);
        commander.build_dependency(build.dependency)?;
        commander.build_script(build.script)?;
        match commander.build_output(build.output) {
            Some(files) => {
                self.prepare_runtime(files, metadata, runtime)?;
                Ok(())
            },
            None => {
                Err( String::from("Installation failed.") )
            }
        }
    }

    pub fn uninstall(&self, name:&String) -> ExecResult {
        let command = Commander::new(self.root.clone(), self.root.clone());
        if let Some(cfg) = self.load_config_file(name) {
            if let Some(ref runtime) = cfg.runtime {
                command.runtime_disable(&runtime.disable)?;
            }
            if let Some(ref metadata) = cfg.metadata {
                let name = &metadata.name;
                command.remove_output(name, &cfg.files);
            }
        }
        Ok(())
    }
}

// service register / unregister / execute / chain_execute
impl FFIManagerStub {
    pub fn register(&mut self, name: &String) -> Option<String> {
        let service_sig = {
            if let Some(sig) = self.service_map.get(name) {
                Some(*sig)
            }
            else {
                let cfg = self.load_config_file(name)?;
                self.load_service(cfg)?;
                self.insert_service_map(name)
            }
        }?;

        let usage_sig = self.insert_usage_map(&service_sig)?; //"None" is always impossible
        let srv_use_sig:u64 = ((service_sig as u64) << 32) + (usage_sig as u64);
        Some( srv_use_sig.to_string() )
    }
    
    pub fn unregister(&mut self, name:&String, srv_use_sig: &String) {
        let srv_use_sig:u64 = srv_use_sig.parse().unwrap_or(0);
        let service_sig = (srv_use_sig >> 32) as u32;   //high u32
        let usage_sig   = srv_use_sig as u32;           //low u32
        
        if let Some(sig) = self.service_map.get(name) {
            if *sig==service_sig {
                if let Some(srv_usage) = self.usage_map.get_mut(&service_sig) {
                    srv_usage.remove(&usage_sig);
                    // cleanup if all usages gone
                    if srv_usage.is_empty() {
                        self.usage_map.remove(&service_sig);
                        self.service_map.remove(name);
                    }
                }
            }
        }
    }
    
    pub fn execute<T>(&self, descriptor:FFIDescriptor, callback:T)
    where T: FnOnce(String) -> (),
    {
        unimplemented!()
    }
    
    pub fn chain_execute<T>(&self, descriptors:Vec<FFIDescriptor>, callback:T)
    where T: FnOnce(String) -> ()
    {
        unimplemented!()
    }
}