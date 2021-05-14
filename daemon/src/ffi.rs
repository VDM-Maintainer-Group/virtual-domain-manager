extern crate libc;

use pyo3::prelude::*;
use std::ffi::{CStr, CString};
use threadpool::ThreadPool;
use serde_json::{self, Value};
use crate::shared_consts::VDM_CAPABILITY_DIR;

// - On-demand load cdll library with "usage count"
//      - load from "~/.vdm/capability" using "ffi.rs"
//      - with "register" command, +1; with "unregister" command, -1
//      - zero for release

type PyFunc = String;

// #[repr(u16)]
enum RawFunc<T,R> {
    Value0(Box<dyn Fn() -> R>),
    Value1(Box<dyn Fn(T) -> R>),
    Value2(Box<dyn Fn(T,T) -> R>),
    Value3(Box<dyn Fn(T,T,T) -> R>),
    Value4(Box<dyn Fn(T,T,T,T) -> R>),
    Value5(Box<dyn Fn(T,T,T,T,T) -> R>)
}

enum Func {
    CFunc(RawFunc<CString, *const libc::c_char>),
    RustFunc(RawFunc<String, String>),
    PythonFunc(PyFunc)
}

pub struct FFIManager {
    pool: ThreadPool
}

impl FFIManager {
    pub fn new() -> FFIManager {
        FFIManager{
            pool: ThreadPool::new(num_cpus::get())
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
