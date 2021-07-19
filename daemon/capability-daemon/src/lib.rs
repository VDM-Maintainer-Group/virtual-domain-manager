mod shmem;
mod consts;
use pyo3::prelude::*;
use crate::consts::*;

use serde_ipc::JsonifyIPC;
use shmem::ShMem;

fn _init() -> JsonifyIPC<ShMem> {
    let root = Some( String::from(VDM_CAPABILITY_DIR) );
    let server_port = Some(VDM_SERVER_PORT);
    JsonifyIPC::<ShMem>::new(root, server_port)
}

#[pymodule]
fn capability_manager(_py:Python, m:&PyModule) -> PyResult<()> {
    #[pyfn(m, "install")]
    fn install_capability(_py: Python, path:String) -> PyResult<String> {
        match _init().install_service(path) {
            Ok(_) => Ok("".into()),
            Err(msg) => Ok(msg)
        }
    }

    #[pyfn(m, "uninstall")]
    fn uninstall_capability(_py: Python, name:String) -> PyResult<String> {
        match _init().uninstall_service(name) {
            Ok(_) => Ok("".into()),
            Err(msg) => Ok(msg)
        }
    }

    #[pyfn(m, "enable")]
    fn enable_capability(_py: Python, name:String) -> PyResult<String> {
        match _init().enable_service(name) {
            Ok(_) => Ok("".into()),
            Err(msg) => Ok(msg)
        }
    }

    #[pyfn(m, "disable")]
    fn disable_capability(_py: Python, name:String) -> PyResult<String> {
        match _init().disable_service(name) {
            Ok(_) => Ok("".into()),
            Err(msg) => Ok(msg)
        }
    }

    #[pyfn(m, "query")]
    fn query_status(_py: Python, name:String) -> PyResult<String> {
        match _init().service_status(name) {
            None => Ok( "N/A".into() ),
            Some(true) => Ok( "Capable".into() ),
            Some(false) => Ok( "Incapable".into() )
        }
    }

    #[pyfn(m, "start_daemon")]
    fn start_daemon(_py: Python) -> PyResult<()> {
        _init().start();
        Ok(())
    }

    #[pyfn(m, "stop_daemon")]
    fn stop_daemon(_py: Python) -> PyResult<()> {
        _init().stop();
        Ok(())
    }

    Ok(())
}
