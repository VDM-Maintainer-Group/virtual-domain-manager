extern crate libc;

// standard library
use std::path::PathBuf;
use std::ffi::CString;
use std::sync::{mpsc, Arc, Mutex};
use std::convert::TryFrom;
use std::net::{SocketAddr,};
use std::collections::BTreeSet;

// third-party crates
use tokio::net::{TcpStream, TcpListener};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::sync::Mutex as TokioMutex;
use threadpool::ThreadPool;
use shared_memory::{Shmem, ShmemConf};
use serde_json::{self, Value};
use num_enum::TryFromPrimitive;

// root crates
use crate::core::ffi::{FFIManager,FFIManager_stub};

// - RPC server response to async event
//      - "connect/disconnect" from client
//      - "register/unregister" from client (with error)
//      - "call/one-way-call/chain-call" from client (with error)

#[allow(dead_code)] //Rust lint open issue, #47133
type ArcFFIManager<'a> = Arc<Mutex<FFIManager<'a>>>;
#[allow(dead_code)] //Rust lint open issue, #47133
type Message = (u32, String);

// const SHM_REQ_MAX_SIZE:usize = 10*1024; //10KB
#[allow(dead_code)] //Rust lint open issue, #47133
const SHM_RES_MAX_SIZE:usize = 1024*1024; //1MB
#[allow(dead_code)] //Rust lint open issue, #47133
const VDM_CLIENT_ID_LEN:usize = 16;

#[allow(non_camel_case_types)]
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

pub struct IpcWorker {}

impl IpcWorker {
    fn _recv_loop(ffi: FFIManager_stub, tx: mpsc::Sender<Message>, shm_req:Shmem, sem_req:*mut libc::sem_t) {
        let mut capability_set: BTreeSet<String> = BTreeSet::new();
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
        Self::_close(sem_req);
    }
    
    fn _send_loop(rx: mpsc::Receiver<Message>, shm_res:Shmem, sem_res:*mut libc::sem_t) {
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
        Self::_close(sem_res);
    }

    fn _close(sem:*mut libc::sem_t) {
        unsafe{ libc::sem_close(sem) };
    }
}

pub struct IPCServer {
    root:PathBuf,
    server_port:u16,
    pool: Arc<TokioMutex<ThreadPool>>
}

impl IPCServer {

    pub fn new(root:PathBuf, server_port:u16) -> Arc<Self> {
        let pool = Arc::new(TokioMutex::new(
            ThreadPool::new(num_cpus::get())
        ));

        Arc::new(IPCServer{
            root, server_port, pool
        })
    }

    fn spawn_send_thread(res_id:String, rx:mpsc::Receiver<Message>) {
        let shm_res = match ShmemConf::new().size(SHM_RES_MAX_SIZE)
            .flink( format!("{}_res", res_id) ).create() {
                Ok(m) => m,
                Err(e) => {
                    eprintln!("Unable to create or open shmem flink: {}", e);
                    return;
                }
            };
        let sem_res = CString::new( format!("/{}_res", res_id) )
            .map_err(|_| format!("CString::new failed"))
            .and_then(|sem_name| {
                match unsafe { libc::sem_open(sem_name.as_ptr(), libc::O_CREAT|libc::O_EXCL, 0o600, 1) } {
                    i if i != libc::SEM_FAILED => Ok(i),
                    _ => Err( format!("sem open failed.") )
                }
            }).unwrap();
        IpcWorker::_send_loop(rx, shm_res, sem_res);
    }

    fn spawn_recv_thread(req_id:String, tx:mpsc::Sender<Message>, ffi:FFIManager_stub) {
        let shm_req = match ShmemConf::new().flink(format!("{}_req", req_id)).open() {
            Ok(m) => m,
            Err(e) => {
                eprintln!("Unable to create or open shmem flink: {}", e);
                return;
            }
        };
        let sem_req = CString::new( format!("/{}_req", req_id) )
            .map_err(|_| format!("CString::new failed"))
            .and_then(|sem_name| {
                match unsafe { libc::sem_open(sem_name.as_ptr(), 0, 0o600, 1) } {
                    i if i != libc::SEM_FAILED => Ok(i),
                    _ => Err( format!("sem open failed.") )
                }
            }).unwrap();
        IpcWorker::_recv_loop(ffi, tx, shm_req, sem_req);
    }

    async fn try_connect(_self: Arc<Self>, mut socket:TcpStream, ffi:FFIManager_stub) {
        let mut buf = [0; VDM_CLIENT_ID_LEN+1];
        let mut id_buf = Vec::<u8>::new();
        let (tx, rx) = mpsc::channel::<Message>();

        // handshake-I(a): recv id
        let n = match socket.read(&mut buf).await {
            Ok(n) => n,
            Err(e) => {
                eprintln!("hs1: failed to write to socket; err = {:?}", e);
                return
            }
        };
        id_buf.extend( buf[..n].iter().copied() );
        let _id = std::str::from_utf8(&id_buf).unwrap();

        // handshake-I(b): spawn "send" thread
        let res_id = format!("{}_res", _id);
        _self.pool.lock().await.execute(move || {
            Self::spawn_send_thread(res_id, rx);
        });

        // handshake-II: write back
        if let Err(e) = socket.write_all(&buf).await {
            eprintln!("hs2: failed to write to socket; err = {:?}", e);
            return;
        }

        // handshake-III: spawn "recv" thread
        if let Err(e) = socket.read(&mut buf).await {
            eprintln!("hs3: failed to read from socket; err = {:?}", e);
            return;
        }
        let req_id = format!("{}_req", _id);
        _self.pool.lock().await.execute(move || {
            Self::spawn_recv_thread(req_id, tx, ffi);
        });
    }

    pub async fn daemon(_self:Arc<Self>) {
        let sock_addr = SocketAddr::new( "127.0.0.1".parse().unwrap(), _self.server_port );
        let listener = TcpListener::bind(sock_addr).await.unwrap();
        // let ffi = Arc::new(Mutex::new( FFIManager::new() )); //global usage

        loop {
            let (socket, _) = listener.accept().await.unwrap();
            let _self = _self.clone();
            let _ffi = FFIManager_stub{};
            // let ffi_ref = ffi.clone();

            tokio::spawn(async move {
                Self::try_connect(_self, socket, _ffi).await
            });
        }

    }

}