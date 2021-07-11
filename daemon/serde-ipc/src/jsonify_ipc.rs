use std::sync::{Arc, Mutex};
use std::path::PathBuf;
// third-party crates
use shellexpand::tilde as expand_user;
use tokio::runtime::Runtime as TokioRuntime;
// root crates
use crate::core::ipc;
use crate::core::ffi;
use crate::core::traits::{Serde, IPCProtocol};

pub struct JsonifyIPC<T>
where T:IPCProtocol
{
    // root: PathBuf,
    server_port: u16,
    rt: TokioRuntime,
    ffi: ffi::ArcFFIManagerStub,
    _protocol: Option<T>, //used for type inference
    server: Option<Arc<Mutex<ipc::IPCServer<T>>>>
}

impl<T> Serde for JsonifyIPC<T>
where T:IPCProtocol
{
    //TODO: implement Serde
}

impl<T> JsonifyIPC<T>
where T: IPCProtocol
{
    /// Return JsonifyIPC handle configured with given:
    /// - (Optional) **path**: the working directory for capability, default is `~/.vdm/libs`
    pub fn new(root:Option<String>, server_port:Option<u16>) -> Self {
        let root = PathBuf::from(
            root.unwrap_or( expand_user("~/.serde_ipc").into_owned() )
        );
        let server_port = server_port.unwrap_or(42000);

        let rt = TokioRuntime::new().unwrap();
        let ffi = Arc::new(Mutex::new(
            ffi::FFIManagerStub::new(root)
        ));
        // let protocol = Arc::new(protocol);
        JsonifyIPC {
            server_port, rt, ffi,
            _protocol:None, server:None
        }
    }

    /// Start the JsonifyIPC daemon waiting for client connection.
    pub fn start(&mut self) {
        let ffi = self.ffi.clone();
        let protocol = self._protocol.clone();

        self.server = Some( ipc::IPCServer::new(
            self.server_port, ffi, protocol.unwrap()
        ) );
        let _server = self.server.clone();

        self.rt.spawn(async move {
            ipc::IPCServer::daemon( _server.unwrap() ).await
        });
    }

    /// Stop the JsonifyIPC daemon by: 1) shutdown all tokio threads; 2) stop IPCServer thread pool.
    pub fn stop(mut self) {
        self.rt.shutdown_background(); //drop occurs here
        self.server = None; //drop occurs here
        //
        self.rt = TokioRuntime::new().unwrap();
    }

    /// Add service via an active IPCServer
    pub fn install_service(&mut self) {
        unimplemented!()
    }

    /// Remove service via an active IPCServer
    pub fn uninstall_service(&mut self) {
        unimplemented!()
    }

    /// Get service via an active IPCServer
    pub fn get_service(&mut self) {
        unimplemented!()
    }
}
