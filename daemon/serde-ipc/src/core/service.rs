extern crate libc;
extern crate libloading;

use std::collections::HashMap;
//
use libc::{c_char};
use std::ffi::{CStr, CString};
use pyo3::prelude::*;
use pyo3::types::*;
//
use crate::core::ffi::{Metadata, MetaFunc};

type PyFuncName = String;
type PyModName = String;

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
            0 => Some( RawFunc::Value0( unsafe{ lib.get(name).ok()? } ) ),
            1 => Some( RawFunc::Value1( unsafe{ lib.get(name).ok()? } ) ),
            2 => Some( RawFunc::Value2( unsafe{ lib.get(name).ok()? } ) ),
            3 => Some( RawFunc::Value3( unsafe{ lib.get(name).ok()? } ) ),
            4 => Some( RawFunc::Value4( unsafe{ lib.get(name).ok()? } ) ),
            5 => Some( RawFunc::Value5( unsafe{ lib.get(name).ok()? } ) ),
            _ => None
        }
    }

    pub fn call(&self, mut args:Vec<T>) -> Option<R>{
        let mut args = args.drain(..);
        match self {
            Self::Value0(func) => Some(
                func()
            ),
            Self::Value1(func) => Some(
                func( args.next()? )
            ),
            Self::Value2(func) => Some(
                func( args.next()?, args.next()? )
            ),
            Self::Value3(func) => Some(
                func( args.next()?, args.next()?, args.next()? )
            ),
            Self::Value4(func) => Some(
                func( args.next()?, args.next()?, args.next()?, args.next()? )
            ),
            Self::Value5(func) => Some(
                func( args.next()?, args.next()?, args.next()?, args.next()?, args.next()? )
            )
        }
    }
}

enum Func<'a> {
    CFunc(RawFunc<'a,*const c_char, *const c_char>),
    RustFunc(RawFunc<'a,String, String>),
    PythonFunc((&'a PyModName, PyFuncName))
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
                Some( Func::PythonFunc( (&lib, name.clone()) ) )
            }
        }
    }

    pub fn call(&self, args:Vec<String>, args_name:Vec<&String>) -> Option<String> {
        match self {
            Self::CFunc(func) => {
                let args:Vec<CString> = args.iter().map(|arg|{
                    CString::new( arg.to_string() ).unwrap()
                }).collect();
                let _args:Vec<*const c_char> = args.iter().map(|arg|{
                    arg.as_ptr()
                }).collect();
                unsafe{ Some(
                    CStr::from_ptr( func.call(_args)? ).to_string_lossy().into_owned()
                ) }
            },
            Self::RustFunc(func) => {
                func.call(args)
            },
            Self::PythonFunc(func) => {
                let (mod_name, func_name) = func;
                Python::with_gil(|py|{
                    let py_module = PyModule::import(py, mod_name).ok()?;
                    let py_func = py_module.getattr(func_name).ok()?;
                    let kwargs:Vec<(String,String)> = args.into_iter().enumerate().map(|(i,v)|{
                        ( args_name[i].to_string(), v )
                    }).collect();
                    let kwargs = kwargs.into_py_dict(py);
                    py_func.call((), Some(kwargs)).ok()?.extract().ok()
                })
            }
        }
    }
}

#[derive(Debug)]
enum LibraryContext {
    CDLL(libloading::Library),
    Rust(libloading::Library),
    Python(PyModName)
}

#[derive(Debug)]
pub struct Service {
    context: LibraryContext,
    func: HashMap<String, MetaFunc>
}

impl Service {
    pub fn load(entry:&String, metadata:Metadata) -> Option<Self> {
        let context = match &metadata.class[..] {
            "c" | "cpp" => {
                if let Ok(lib) = unsafe{ libloading::Library::new(entry) } {
                    Some( LibraryContext::CDLL(lib) )
                } else { None }
            },
            "rust" => {
                if let Ok(lib) = unsafe{ libloading::Library::new(entry) } {
                    Some( LibraryContext::Rust(lib) )
                } else { None }
            },
            "python" => {
                if let Ok(contents) = std::fs::read_to_string(entry) {
                    let module_name = std::path::Path::new(entry).file_name()?.to_str()?;
                    Python::with_gil(|py|{
                        let _py_module = PyModule::from_code(py, &contents, "__internal_file__", module_name).ok();
                    });
                    Some( LibraryContext::Python(module_name.into()) )
                } else { None }
            },
            _ => { None }
        };
        let func = metadata.func;

        if let Some(context) = context {
            Some(
                Service{ context, func }
            )
        } else {None}
    }

    pub fn call(&self, name:&String, args:Vec<String>) -> Option<String> {
        let func = self.func.get(name)?;
        let argc = func.args.len();
        let args_name:Option<Vec<&String>> = func.args.iter().map(|arg|{
            Some( arg.iter().nth(0)?.0 )
        }).collect();
        Func::new(&self.context, name, argc)?.call(args, args_name?)
    }
}
