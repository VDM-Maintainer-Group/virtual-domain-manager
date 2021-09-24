mod consts;
mod shmem;
use pyo3::prelude::*;
use crate::consts::*;

use serde_ipc::JsonifyIPC;
use crate::shmem::ShMem;

#[pyclass]
struct CapabilityDaemon {
    server: JsonifyIPC
}

#[pymethods]
impl CapabilityDaemon {
    #[new]
    fn new(root:Option<String>, port:Option<u16>) -> Self {
        let root = Some( root.unwrap_or(VDM_CAPABILITY_DIR.into()) );
        let server_port = Some( port.unwrap_or(VDM_SERVER_PORT) );
        let server = JsonifyIPC::new(root, server_port);
        CapabilityDaemon{ server }
    }

    #[pyo3(name = "install")]
    fn install_capability(&self, path:String) -> PyResult<String> {
        match self.server.install_service(path) {
            Ok(_) => Ok("".into()),
            Err(msg) => Ok(msg)
        }
    }

    #[pyo3(name = "uninstall")]
    fn uninstall_capability(&self, name:String) -> PyResult<String> {
        match self.server.uninstall_service(name) {
            Ok(_) => Ok("".into()),
            Err(msg) => Ok(msg)
        }
    }

    #[pyo3(name = "enable")]
    fn enable_capability(&self, name:String) -> PyResult<String> {
        match self.server.enable_service(name) {
            Ok(_) => Ok("".into()),
            Err(msg) => Ok(msg)
        }
    }

    #[pyo3(name = "disable")]
    fn disable_capability(&self, name:String) -> PyResult<String> {
        match self.server.disable_service(name) {
            Ok(_) => Ok("".into()),
            Err(msg) => Ok(msg)
        }
    }

    #[pyo3(name = "query")]
    fn query_status(&self, name:String) -> PyResult<String> {
        match self.server.service_status(name) {
            None => Ok( "N/A".into() ),
            Some(true) => Ok( "Capable".into() ),
            Some(false) => Ok( "Incapable".into() )
        }
    }

    #[pyo3(name = "start_daemon")]
    fn start_daemon(&mut self) -> PyResult<()> {
        self.server.start::<ShMem>();
        Ok(())
    }
}

#[pymodule]
fn vdm_capability_daemon(_py:Python, m:&PyModule) -> PyResult<()> {
    m.add_class::<CapabilityDaemon>()?;
    Ok(())
}
