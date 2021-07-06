use std::sync::{Arc, Mutex};
use std::path::PathBuf;
// third-party crates
use shellexpand::tilde as expand_user;
use tokio::runtime::Runtime as TokioRuntime;
// root crates
use crate::core::ipc;
use crate::core::ffi;
use crate::core::traits;

pub struct JsonifyIPC {
    // root: PathBuf,
    server_port: u16,
    rt: TokioRuntime,
    ffi: ffi::ArcFFIManagerStub,
    server: Option<Arc<ipc::IPCServer>>
}

impl traits::Serde for JsonifyIPC {
    //TODO: implement Serde
}

impl JsonifyIPC {
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
        JsonifyIPC {
            server_port, rt, ffi, server:None
        }
    }

    /// Start the JsonifyIPC daemon waiting for client connection.
    pub fn start(&mut self) {
        self.server = Some( ipc::IPCServer::new(self.server_port) );
        let _server = self.server.clone();
        let _ffi = self.ffi.clone();

        self.rt.spawn(async move {
            ipc::IPCServer::daemon( _server.unwrap(), _ffi ).await
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
