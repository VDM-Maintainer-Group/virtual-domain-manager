extern crate libc;

use threadpool::ThreadPool;
use serde_json::{self, Value};
use crate::shared_consts::VDM_CAPABILITY_DIR;

// - On-demand load cdll library with "usage count"
//      - load from "~/.vdm/capability" using "ffi.rs"
//      - with "register" command, +1; with "unregister" command, -1
//      - zero for release

pub struct FFIManager {
    pool: ThreadPool
}

impl FFIManager {
    pub fn new() -> FFIManager {
        FFIManager{
            pool: ThreadPool::new(num_cpus::get())
        }
    }

    pub fn register(&mut self, name: &str) -> Option<String> {
        unimplemented!();
    }

    pub fn unregister(&mut self, name: &str) {
        unimplemented!();
    }

    pub fn execute<T>(&mut self, raw_data:String, callback:T)
    where T: FnOnce(String) -> ()
    {
        let v: Value = serde_json::from_slice(raw_data.as_bytes()).unwrap();
        let sig  = v["sig"].as_str().unwrap();
        let func = v["func"].as_str().unwrap();
        let ref args:Value = v["args"];
        unimplemented!();
    }

    pub fn chain_execute<T>(&mut self, raw_data:String, callback:T)
    where T: FnOnce(String) -> ()
    {
        // sig_func_args_table:&Value
    }
}
