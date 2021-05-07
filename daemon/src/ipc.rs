extern crate libc;

use std::ffi::CString;
use std::thread;
use threadpool::ThreadPool;
use std::sync::{mpsc, Arc, Mutex};
//
use tokio::net::TcpListener;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
//
use serde_json as json;
use shared_memory::{Shmem, ShmemConf};
use crate::shared_consts::VDM_SERVER_ADDR;
// - RPC server response to async event
//      - "connect/disconnect" from client
//      - "register/unregister" from client (with error)
//      - "call/one-way-call/chain-call" from client (with error)
//      - execute function asynchronously and stateless

type ArcThreadPool = Arc<Mutex<ThreadPool>>;
type Message = (u32, json::Value);

// const SHM_REQ_MAX_SIZE:usize = 10*1024; //10KB
#[allow(dead_code)] //Rust lint open issue, #47133
const SHM_RES_MAX_SIZE:usize = 1024*1024; //1MB
#[allow(dead_code)] //Rust lint open issue, #47133
const VDM_CLIENT_ID_LEN:usize = 16;

#[allow(non_camel_case_types)]
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

fn recv_loop(pool: ArcThreadPool, tx: mpsc::Sender<Message>, shm_req:Shmem, sem_req:*mut libc::sem_t) {
    let _result = move || -> Result<(), Box<dyn std::error::Error>> {
        loop {
            // acquire the lock
            if unsafe{ libc::sem_wait(sem_req) } != 0 {
                break Ok(())
            }
            // load data from shm_req
            let slice = unsafe{ shm_req.as_slice() };
            // slice[..ResHeader.size]
            // release the lock
            if unsafe{ libc::sem_post(sem_req) } < 0 {
                break Ok(());
            }
        }
    };
    close(shm_req, sem_req);
}

fn send_loop(rx: mpsc::Receiver<Message>, shm_res:Shmem, sem_res:*mut libc::sem_t) {
    let _result = move || -> Result<(), Box<dyn std::error::Error>> {
        loop {

        }
    };
    close(shm_res, sem_res);
}

fn close(shm:Shmem, sem:*mut libc::sem_t) {
    unsafe{ libc::sem_close(sem) };
}

#[tokio::main]
pub async fn daemon() -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind(VDM_SERVER_ADDR).await?;
    let pool = Arc::new(Mutex::new( ThreadPool::new(num_cpus::get()) ));

    loop {
        let (mut socket, _) = listener.accept().await?;
        let pool_ref = pool.clone();

        tokio::spawn(async move {
            let mut buf = [0; VDM_CLIENT_ID_LEN+1];
            let (tx, rx) = mpsc::channel::<Message>();

            // handshake-I: recv id and start "send" thread
            let n = match socket.read(&mut buf).await {
                Ok(n) if n==0 => return,
                Ok(n) => n,
                Err(e) => {
                    eprintln!("hs1: failed to read from socket; err = {:?}", e);
                    return;
                }
            };
            let mut _tmp = Vec::new();
            _tmp.extend( buf[..n].iter().copied() );
            let res_id = String::from_utf8(_tmp).unwrap();
            let req_id = res_id.clone();
            thread::spawn(move || {
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
                send_loop(rx, shm_res, sem_res);
            });

            // handshake-II: write back
            if let Err(e) = socket.write_all(&buf).await {
                eprintln!("hs2: failed to write to socket; err = {:?}", e);
                return;
            }

            // handshake-III: start "recv" thread
            if let Err(e) = socket.read(&mut buf).await {
                eprintln!("hs3: failed to read from socket; err = {:?}", e);
                return;
            }
            thread::spawn(move || {
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
                recv_loop(pool_ref, tx, shm_req, sem_req);
            });
        });
    }

}