
extern crate errno;
extern crate libc;

mod ipc_daemon {
    use std::str;
    use std::ffi::CString;
    use std::thread;
    use tokio::net::TcpListener;
    use tokio::io::{AsyncReadExt, AsyncWriteExt};
    use shared_memory::{Shmem, ShmemConf};
    // - RPC server response to async event
    //      - "connect/disconnect" from client
    //      - "register/unregister" from client (with error)
    //      - "call/one-way-call/chain-call" from client (with error)
    //      - execute asynchronously and stateless in separated thread
    // - On-demand load cdll library with "usage count"
    //      - load from "~/.vdm/capability" using "ffi.rs"
    //      - with "register" command, +1; with "unregister" command, -1
    //      - zero for release
    const SHM_REQ_MAX_SIZE:usize = 10*1024; //10KB
    const SHM_RES_MAX_SIZE:usize = 1024*1024; //1MB
    const VDM_SERVER_ADDR:&str = "127.0.0.1:42000";
    const VDM_CLIENT_ID_LEN:usize = 16;
    // ALIVE       = 0x00
    // REGISTER    = 0x01
    // UNREGISTER  = 0x02
    // CALL        = 0x03
    // ONE_WAY     = 0x04
    // CHAIN_CALL  = 0x05

    fn send_loop(shm_res:Shmem, sem_res:*mut libc::sem_t) {
        loop {

        }
    }

    fn recv_loop(shm_req:Shmem, sem_req:*mut libc::sem_t) {
        loop {

        }
    }

    #[tokio::main]
    pub async fn daemon() -> Result<(), Box<dyn std::error::Error>> {
        let mut listener = TcpListener::bind(VDM_SERVER_ADDR).await?;

        loop {
            let (mut socket, _) = listener.accept().await?;
            tokio::spawn(async move {
                let mut buf = [0; VDM_CLIENT_ID_LEN+1];
                // handshake-I: recv id and start "send" thread
                let n = match socket.read(&mut buf).await {
                    Ok(n) if n==0 => return,
                    Ok(n) => n,
                    Err(e) => {
                        eprintln!("hs1: failed to read from socket; err = {:?}", e);
                        return;
                    }
                };
                let _id = str::from_utf8(&buf[..n]).unwrap();
                thread::spawn(move || {
                    let shm_res = match ShmemConf::new().size(SHM_RES_MAX_SIZE)
                        .flink( format!("{}_res", _id) ).create() {
                            Ok(m) => m,
                            Err(e) => {
                                eprintln!("Unable to create or open shmem flink: {}", e);
                                return;
                            }
                        };
                    let sem_res = CString::new( format!("/{}_res", _id) )
                        .and_then(|sem_name| {
                            match unsafe { libc::sem_open(sem_name.as_ptr(), libc::O_CREAT|libc::O_EXCL, 0o600, 1) } {
                                libc::SEM_FAILED => {
                                    let e = errno::errno();
                                    Err(format!("sem_open {}: {}", e.0, e))
                                },
                                i if i != libc::SEM_FAILED => {
                                    Ok(i)
                                }
                            }
                        }).unwrap();
                    send_loop(shm_res, sem_res);
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
                let _id = str::from_utf8(&buf[..n]).unwrap();
                thread::spawn(move || {
                    let shm_req = match ShmemConf::new().flink(format!("{}_req", _id)).open() {
                        Ok(m) => m,
                        Err(e) => {
                            eprintln!("Unable to create or open shmem flink: {}", e);
                            return;
                        }
                    };
                    let sem_req = CString::new( format!("/{}_req", _id) )
                        .and_then(|sem_name| {
                            match unsafe { libc::sem_open(sem_name.as_ptr(), 0, 0o600, 1) } {
                                libc::SEM_FAILED => {
                                    let e = errno::errno();
                                    Err(format!("sem_open {}: {}", e.0, e))
                                },
                                i if i != libc::SEM_FAILED => {
                                    Ok(i)
                                }
                            }
                        }).unwrap();
                    recv_loop(shm_req, sem_req);
                });
            });
        }

    }
}

fn main() {
    // call on ipc_daemon with async event
}