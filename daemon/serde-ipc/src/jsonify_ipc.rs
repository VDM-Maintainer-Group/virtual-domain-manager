use std::path::PathBuf;
// third-party crates
use shellexpand::tilde as expand_user;
use tokio::runtime::Runtime as TokioRuntime;
// root crates
use crate::core::ipc;

pub struct JsonifyIPC {
    root: PathBuf,
    server_port: u16,
    rt: TokioRuntime
}

impl JsonifyIPC {
    /// Return JsonifyIPC handle configured with given:
    /// - (Optional) **path**: the working directory for capability, default is `~/.vdm/libs`
    pub fn new(root:Option<String>, server_port:Option<u16>) -> Self {
        let root = PathBuf::from(
            root.unwrap_or( expand_user("~/.vdm/libs").into_owned() )
        );
        let server_port = server_port.unwrap_or(42000);
        let rt = TokioRuntime::new().unwrap();

        JsonifyIPC {
            root, server_port, rt
        }
    }

    /// Start the JsonifyIPC daemon waiting for client connection.
    pub fn start(&self) {
        let server = ipc::IPCServer::new( self.root.clone(), self.server_port );
        self.rt.block_on(async move {
            server.daemon().await
        }).unwrap();
    }

    /// Stop the JsonifyIPC daemon by: 1) shutdown all tokio threads; 2) stop IPCServer thread pool.
    pub fn stop(mut self) {
        self.rt.shutdown_background();
        self.rt = TokioRuntime::new().unwrap();
        //TODO: stop IPCServer thread pool
    }
}
