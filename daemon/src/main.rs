
extern crate libc;

mod ipc_daemon {
    use tokio::net::TcpListener;
    use tokio::io::{AsyncReadExt, AsyncWriteExt};
    // - RPC server response to async event
    //      - "connect/disconnect" from client
    //      - "register/unregister" from client (with error)
    //      - "call/one-way-call/chain-call" from client (with error)
    //      - execute asynchronously and stateless in separated thread
    // - On-demand load cdll library with "usage count"
    //      - load from "~/.vdm/capability" using "ffi.rs"
    //      - with "register" command, +1; with "unregister" command, -1
    //      - zero for release
    const SHM_REQ_MAX_SIZE:i32 = 10*1024; //10KB
    const SHM_RES_MAX_SIZE:i32 = 1024*1024; //1MB
    const VDM_SERVER_ADDR:&str = "127.0.0.1:42000";
    const VDM_CLIENT_ID_LEN:usize = 16;
    // ALIVE       = 0x00
    // REGISTER    = 0x01
    // UNREGISTER  = 0x02
    // CALL        = 0x03
    // ONE_WAY     = 0x04
    // CHAIN_CALL  = 0x05

    #[tokio::main]
    pub async fn daemon() -> Result<(), Box<dyn std::error::Error>> {
        let mut listener = TcpListener::bind(VDM_SERVER_ADDR).await?;

        loop {
            let (mut socket, _) = listener.accept().await?;
            tokio::spawn(async move {
                let mut buf = [0; VDM_CLIENT_ID_LEN+1];
                
            });
        }

    }
}

fn main() {
    // call on ipc_daemon with async event
}