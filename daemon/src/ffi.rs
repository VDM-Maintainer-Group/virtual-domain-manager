extern crate libc;

use threadpool::ThreadPool;
use serde_json as json;
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
}
