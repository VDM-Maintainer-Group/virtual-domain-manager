extern crate libc;

use std::ops::Deref;
use std::path::Path;
use std::collections::HashMap;
use pyo3::prelude::*;
use libc::{c_char};
use std::ffi::{CStr, CString};
use threadpool::ThreadPool;
use serde_json::{self, Value};
//
use crate::shared_consts::VDM_CAPABILITY_DIR;

// - On-demand load cdll library with "usage count"
//      - load from "~/.vdm/capability" using "ffi.rs"
//      - with "register" command, +1; with "unregister" command, -1
//      - zero for release

type PyFunc = String;
type Library = HashMap<String, Func>;

// #[repr(u16)]
enum RawFunc<T,R>
{
    Value0(Box<dyn Fn()->R + Send>),
    Value1(Box<dyn Fn(T)->R + Send>),
    Value2(Box<dyn Fn(T,T)->R + Send>),
    Value3(Box<dyn Fn(T,T,T)->R + Send>),
    Value4(Box<dyn Fn(T,T,T,T)->R + Send>),
    Value5(Box<dyn Fn(T,T,T,T,T)->R + Send>)
}

impl<T,R> RawFunc<T,R> {
    pub fn call(&self, mut args:Vec<T>) -> Result<R, Box<dyn std::error::Error>>{
        let mut iter = args.drain(..);
        match self {
            Self::Value0(func) => {
                Ok(func())
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

enum Func {
    CFunc(RawFunc<*const c_char, *const c_char>),
    RustFunc(RawFunc<String, String>),
    PythonFunc(PyFunc)
}

impl Func {
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
                String::new()
            }
        }
    }
}

pub struct FFIManager {
    root: String,
    pool: ThreadPool,
    library: HashMap<String, (u32, Library)>
}

impl FFIManager {
    pub fn new() -> FFIManager {
        FFIManager{
            root: shellexpand::tilde(VDM_CAPABILITY_DIR).into_owned(),
            pool: ThreadPool::new(num_cpus::get()),
            library: HashMap::new()
        }
    }

    pub fn preload(&mut self) {
        unimplemented!();
    }

    pub fn load(&mut self, manifest:&str) {
        unimplemented!();
    }

    pub fn register(&mut self, name: &str) -> Option<String> {
        unimplemented!();
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
