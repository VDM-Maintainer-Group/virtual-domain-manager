use std::sync::{mpsc, Arc, Mutex};
use std::ffi::CString;
use std::convert::TryFrom;
use std::collections::BTreeSet;
//
use num_enum::TryFromPrimitive;
use shared_memory::{Shmem, ShmemConf};
use serde_json::{self, Value};
use threadpool::ThreadPool;
//
use serde_ipc::{ArcFFIManagerStub};
use serde_ipc::IPCProtocol;

type Message = (u32, String);

// const SHM_REQ_MAX_SIZE:usize = 10*1024; //10KB
#[allow(dead_code)] //Rust lint open issue, #47133
const SHM_RES_MAX_SIZE:usize = 1024*1024; //1MB

#[derive(Debug, Eq, PartialEq, TryFromPrimitive)]
#[repr(u16)]
enum Command {
    ALIVE       = 0x00,
    REGISTER    = 0x01,
    UNREGISTER  = 0x02,
    CALL        = 0x03,
    ONE_WAY     = 0x04,
    CHAIN_CALL  = 0x05
}

#[repr(C,packed)]
struct ReqHeader {
    seq: u32,
    command: u16,
    size: u16
}

#[repr(C,packed)]
struct ResHeader {
    seq: u32,
    size: u32
}

unsafe fn volatile_copy<T>(src: *const T, len: usize) -> Vec<T> {
    let mut result = Vec::with_capacity(len);
    let mut tmp_ptr = src; //copy
    loop {
        result.push( std::ptr::read_volatile(tmp_ptr) );
        tmp_ptr = tmp_ptr.add(1);
        if tmp_ptr >= src.add(len) {
            break result
        }
    }
}

fn _recv_loop(ffi: ArcFFIManagerStub, tx: mpsc::Sender<Message>, req_id: String) {
    let mut capability_set: BTreeSet<String> = BTreeSet::new();
    let shm_req = match ShmemConf::new().flink( &req_id ).open() {
        Ok(m) => m,
        Err(e) => {
            eprintln!("Unable to create or open shmem flink: {}", e);
            return;
        }
    };
    let sem_req = CString::new( format!("/{}", req_id) )
        .map_err(|_| format!("CString::new failed"))
        .and_then(|sem_name| {
            match unsafe { libc::sem_open(sem_name.as_ptr(), 0, 0o600, 1) } {
                i if i != libc::SEM_FAILED => Ok(i),
                _ => Err( format!("sem open failed.") )
            }
        }).unwrap();

    let _result = || -> Result<(), Box<dyn std::error::Error>> {
        loop {
            // acquire the lock
            if unsafe{ libc::sem_wait(sem_req) } != 0 {
                break Ok(()) //connection drop happened
            }
            // load data from shm_req
            let raw_ptr = shm_req.as_ptr(); //FIXME: check alive before use
            let req_header_len = std::mem::size_of::<ReqHeader>();
            let req_header:ReqHeader = unsafe{
                let _header = volatile_copy(raw_ptr, req_header_len);
                std::mem::transmute( &_header.as_ptr() )
            };
            let req_data = unsafe{ volatile_copy(raw_ptr.add(req_header_len), req_header.size as usize) };
            let req_data = String::from_utf8(req_data).unwrap(); //panic as you like
            // release the lock
            if unsafe{ libc::sem_post(sem_req) } < 0 {
                break Ok(()) //connection drop happened
            }
            // match command with its response
            if let Ok(command) = Command::try_from(req_header.command) {
                match command {
                    Command::ALIVE => {
                        //synchronized call
                        tx.send( (req_header.seq, String::new()) )?;
                    },
                    Command::REGISTER => {
                        //synchronized call
                        let v: Value = serde_json::from_slice(req_data.as_bytes()).unwrap(); //panic as you like
                        if let Value::String(ref name) = v["name"] {
                            if let Ok(mut ffi_obj) = ffi.lock() {
                                if let Some(cid) = ffi_obj.register(name) {
                                    capability_set.insert( cid.clone() );
                                    tx.send( (req_header.seq, cid) )?;
                                }
                            }
                        }
                    },
                    Command::UNREGISTER => {
                        //synchronized call
                        let v: Value = serde_json::from_slice(req_data.as_bytes()).unwrap(); //panic as you like
                        if let Value::String(ref name) = v["name"] {
                            if capability_set.contains(name) {
                                if let Ok(mut ffi_obj) = ffi.lock() {
                                    ffi_obj.unregister(name);
                                    capability_set.remove(name);
                                }
                            }
                        }
                    },
                    Command::CALL => {
                        let tx_ref = tx.clone();
                        if let Ok(ffi_obj) = ffi.lock() {
                            ffi_obj.execute(req_data, move |res| {
                                tx_ref.send( (req_header.seq, res) ).unwrap_err();
                            });
                        }                        
                    },
                    Command::ONE_WAY => {
                        if let Ok(ffi_obj) = ffi.lock() {
                            ffi_obj.execute(req_data, |_|{}); //no callback for one-way
                        }
                    },
                    Command::CHAIN_CALL => {
                        let tx_ref = tx.clone();
                        if let Ok(ffi_obj) = ffi.lock() {
                            ffi_obj.chain_execute(req_data, move |res| {
                                tx_ref.send( (req_header.seq, res) ).unwrap_err();
                            })
                        }
                    }
                }
            }
        }
    };
    // finalization after connection drop
    if let Ok(mut ffi_obj) = ffi.lock() {
        for name in &capability_set {
            ffi_obj.unregister(name);
        }
    }
    _close(sem_req);
}

fn _send_loop(rx: mpsc::Receiver<Message>, res_id: String) {
    let shm_res = match ShmemConf::new().size(SHM_RES_MAX_SIZE).flink( &res_id ).create() {
        Ok(m) => m,
        Err(e) => {
            eprintln!("Unable to create or open shmem flink: {}", e);
            return;
        }
    };

    let sem_res = CString::new( format!("/{}", res_id) )
        .map_err(|_| format!("CString::new failed"))
        .and_then(|sem_name| {
            match unsafe { libc::sem_open(sem_name.as_ptr(), libc::O_CREAT|libc::O_EXCL, 0o600, 1) } {
                i if i != libc::SEM_FAILED => Ok(i),
                _ => Err( format!("sem open failed.") )
            }
        }).unwrap();

    let _result = || -> Result<(), Box<dyn std::error::Error>> {
        while let Ok(_message) = rx.recv() {
            // acquire the lock
            if unsafe{ libc::sem_wait(sem_res) } != 0 {
                break;
            }
            {
                let (seq, data) = _message;
                let data = data.as_bytes();
                let size = data.len() as u32;
                let buffer = unsafe{
                    let res_header = ResHeader{seq, size};
                };
                //TODO: write volatile to shared memory
            }
            // release the lock
            if unsafe{ libc::sem_post(sem_res) } < 0 {
                break;
            }
        }
        Ok(())
    };
    _close(sem_res);
}

fn _close(sem:*mut libc::sem_t) {
    unsafe{ libc::sem_close(sem) };
}

#[derive(Clone)]
pub struct ShMem {
    uid: String,
    ffi: Option<ArcFFIManagerStub>,
    pool: Arc<Mutex<ThreadPool>>
}

impl IPCProtocol for ShMem {
    type Message = (u32, String);

    fn new(uid:String, ffi:ArcFFIManagerStub) -> Self {
        let ffi = Some(ffi);
        let pool = Arc::new(Mutex::new(
            ThreadPool::new(2)
        ));
        Self{ uid, ffi, pool }
    }

    fn is_alive(&self) -> bool {
        if let Ok(pool_obj) = self.pool.lock() {
            pool_obj.active_count() < 2
        }
        else {
            false
        }
    }

    fn stop(&self) {
        //stop when the pool is dropped.
    }

    fn spawn_send_thread(&mut self, rx: mpsc::Receiver<Self::Message>) {
        let res_id = format!("{}_res", self.uid);
        
        if let Ok(pool_obj) = self.pool.lock() {
            pool_obj.execute(move || {
                _send_loop(rx, res_id);
            });
        }
    }

    fn spawn_recv_thread(&mut self, tx: mpsc::Sender<Self::Message>) {
        let ffi = self.ffi.clone();
        let req_id = format!("{}_req", self.uid);
        
        if let Ok(pool_obj) = self.pool.lock() {
            pool_obj.execute(move || {
                _recv_loop(ffi.unwrap(), tx, req_id);
            });
        }
    }

}
