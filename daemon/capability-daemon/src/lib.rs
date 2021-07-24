mod consts;
mod shmem;
use pyo3::prelude::*;
use crate::consts::*;

use serde_ipc::JsonifyIPC;
use crate::shmem::ShMem;

fn _init() -> JsonifyIPC<ShMem> {
    let root = Some( String::from(VDM_CAPABILITY_DIR) );
    let server_port = Some(VDM_SERVER_PORT);
    JsonifyIPC::<ShMem>::new(root, server_port)
}

#[pyfunction]#[pyo3(name = "install")]
fn install_capability(_py: Python, path:String) -> PyResult<String> {
    match _init().install_service(path) {
        Ok(_) => Ok("".into()),
        Err(msg) => Ok(msg)
    }
}

#[pyfunction]#[pyo3(name = "uninstall")]
fn uninstall_capability(_py: Python, name:String) -> PyResult<String> {
    match _init().uninstall_service(name) {
        Ok(_) => Ok("".into()),
        Err(msg) => Ok(msg)
    }
}

#[pyfunction]#[pyo3(name = "enable")]
fn enable_capability(_py: Python, name:String) -> PyResult<String> {
    match _init().enable_service(name) {
        Ok(_) => Ok("".into()),
        Err(msg) => Ok(msg)
    }
}

#[pyfunction]#[pyo3(name = "disable")]
fn disable_capability(_py: Python, name:String) -> PyResult<String> {
    match _init().disable_service(name) {
        Ok(_) => Ok("".into()),
        Err(msg) => Ok(msg)
    }
}

#[pyfunction]#[pyo3(name = "query")]
fn query_status(_py: Python, name:String) -> PyResult<String> {
    match _init().service_status(name) {
        None => Ok( "N/A".into() ),
        Some(true) => Ok( "Capable".into() ),
        Some(false) => Ok( "Incapable".into() )
    }
}

#[pyfunction]#[pyo3(name = "start_daemon")]
fn start_daemon(_py: Python) -> PyResult<()> {
    _init().start();
    Ok(())
}

#[pyfunction]#[pyo3(name = "stop_daemon")]
fn stop_daemon(_py: Python) -> PyResult<()> {
    _init().stop();
    Ok(())
}

#[pymodule]
fn vdm_capability_daemon(_py:Python, m:&PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(install_capability, m)?)?;
    m.add_function(wrap_pyfunction!(uninstall_capability, m)?)?;
    m.add_function(wrap_pyfunction!(enable_capability, m)?)?;
    m.add_function(wrap_pyfunction!(disable_capability, m)?)?;
    m.add_function(wrap_pyfunction!(query_status, m)?)?;
    m.add_function(wrap_pyfunction!(start_daemon, m)?)?;
    m.add_function(wrap_pyfunction!(stop_daemon, m)?)?;
    Ok(())
}
