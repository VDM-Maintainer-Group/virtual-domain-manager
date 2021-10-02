mod consts;
use pyo3::prelude::*;
use serde::{Serialize,Deserialize};
use crate::consts::*;

use serde_ipc::{FFIManager, MetaFuncMap};
use serde_ipc::{JsonifyIPC, protocol::shmem};

#[derive(Serialize,Deserialize)]
struct NameCallRes {
    sig: String,
    spec: Option<MetaFuncMap>
}

#[pyclass]
struct CapabilityDaemon {
    server: JsonifyIPC,
    ffi_sa: FFIManager 
}

#[pymethods]
impl CapabilityDaemon {
    #[new]
    fn new(root:Option<String>, port:Option<u16>) -> Self {
        let root = Some( root.unwrap_or(VDM_CAPABILITY_DIR.into()) );
        let server_port = Some( port.unwrap_or(VDM_SERVER_PORT) );
        let server = JsonifyIPC::new(root.clone(), server_port);

        let root = std::path::PathBuf::from( shellexpand::tilde(&root.unwrap()).into_owned() );
        let ffi_sa = FFIManager::new(root);
        
        CapabilityDaemon{ server, ffi_sa }
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
        self.server.start::<shmem::ShMem>();
        Ok(())
    }

    #[pyo3(name = "register")]
    fn register(&mut self, name:String) -> PyResult<Option<String>> {
        let mut result_fn = ||{
            let (sig, spec) = self.ffi_sa.register(&name)?;
            serde_json::to_string(&NameCallRes{sig,spec}).ok()
        };

        Ok( result_fn() )
    }

    #[pyo3(name = "unregister")]
    fn unregister(&mut self, name:String, srv_use_sig:String) -> PyResult<()> {
        self.ffi_sa.unregister(&name, &srv_use_sig);
        Ok(())
    }

    #[pyo3(name = "call")]
    fn call(&self, sig:String, func:String, args:Vec<String>) -> PyResult<Option<String>> {
        if let Some(service) = self.ffi_sa.get_service_by_sig(&sig)
        {
            Ok( service.call(&func, args) )
        } else { Ok(None) }
    }
}

#[pymodule]
fn vdm_capability_daemon(_py:Python, m:&PyModule) -> PyResult<()> {
    m.add_class::<CapabilityDaemon>()?;
    Ok(())
}
