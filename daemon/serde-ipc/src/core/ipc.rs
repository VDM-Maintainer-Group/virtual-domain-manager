extern crate libc;

// standard library
use std::sync::{mpsc, Arc, Mutex};
use std::net::{SocketAddr,};
// third-party crates
use tokio::net::{TcpStream, TcpListener};
use tokio::io::{AsyncReadExt, AsyncWriteExt};

// root crates
use crate::core::ffi::ArcFFIManager;
use crate::core::traits::IPCProtocol;

const VDM_CLIENT_ID_LEN:usize = 16;

pub struct IPCServer<P>
where P:IPCProtocol
{
    server_port:u16,
    ffi: ArcFFIManager,
    conns: Vec<P>
}

impl<P> IPCServer<P>
where P:IPCProtocol
{
    pub fn new(server_port:u16, ffi: ArcFFIManager) -> Arc<Mutex<Self>> {
        Arc::new(Mutex::new(
            IPCServer{
                server_port, ffi, conns:Vec::new()
            }
        ))
    }

    async fn try_connect(_self: Arc<Mutex<Self>>, mut socket:TcpStream) -> Result<(),String>
    {
        let mut buf = [0; VDM_CLIENT_ID_LEN+1];
        let mut id_buf = Vec::<u8>::with_capacity(VDM_CLIENT_ID_LEN);
        let (tx, rx) = mpsc::channel::< P::Message >();
        let peer_port = socket.peer_addr().unwrap().port();

        // handshake-I(a): recv id
        let n = match socket.read(&mut buf).await {
            Ok(n) if n==VDM_CLIENT_ID_LEN => Ok(n),
            Ok(_) | Err(_) => {
                Err( format!("[peer:{}] Phase-I handshake failed.", peer_port) )
            }
        }?;
        id_buf.extend( buf[..n].iter().copied() );
        let _id = std::str::from_utf8(&id_buf)
            .map_err( |_|{format!("[peer:{}] Phase-I ID parse failed.", peer_port)} )?;
        let mut _protocol = {
            if let Ok(mut _self) = _self.lock() {
                let ffi = _self.ffi.clone();
                Some( P::new(format!("{}", _id), ffi) )
            } else {None}
        }.ok_or( format!("[peer:{}] Phase-I protocol init failed.", peer_port) )?;

        // handshake-I(b): spawn "send" thread
        _protocol.spawn_send_thread(rx);

        // handshake-II: write back
        socket.write_all(&buf).await.map_err(|_| {
            format!("[peer:{}] Phase-II handshake failed.", peer_port) })?;

        // handshake-III: spawn "recv" thread
        socket.read(&mut buf).await.map_err(|_| {
            format!("[peer:{}] Phase-III handshake failed.", peer_port) })?;
        _protocol.spawn_recv_thread(tx);

        // try to record this connection
        match _self.lock() {
            Ok(mut _self) => {
                _self.conns.push( _protocol );
                Ok(())
            },
            Err(_) => {
                _protocol.stop();
                Err( format!("[peer:{}] Phase-III conn record failed.", peer_port) )
            }
        }
    }

    pub async fn daemon(_self:Arc<Mutex<Self>>)
    {
        let sock_addr = {
            if let Ok(self_obj) = _self.lock() {
                Some(SocketAddr::new( "127.0.0.1".parse().unwrap(), self_obj.server_port ))
            } else {None}
        }.unwrap();
        let listener = TcpListener::bind(sock_addr).await.unwrap();

        loop {
            let (socket, _) = match listener.accept().await {
                Ok(conn) => conn,
                Err(_) => continue
            };
            let _self = _self.clone();

            //cleanup (the first stopped) before connect
            if let Ok(mut _self) = _self.lock() {
                if let Some(pos) = _self.conns.iter().position(|x| !x.is_alive()) {
                    _self.conns.remove(pos);
                }
            }

            tokio::spawn(async move {
                if let Err(msg) = Self::try_connect(_self, socket).await {
                    eprintln!("{}", msg);
                }
            });
        }

    }
}
