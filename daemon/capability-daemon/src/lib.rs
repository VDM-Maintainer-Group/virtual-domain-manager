mod shmem;
mod shared_consts;
use pyo3::prelude::*;
// use pyo3::wrap_pyfunction;
// use crate::shared_consts::VDM_CAPABILITY_DIR;

use serde_ipc::JsonifyIPC;
use shmem::ShMem;

#[pymodule]
fn capability_manager(_py:Python, m:&PyModule) -> PyResult<()> {
    #[pyfn(m, "install")]
    fn install_capability(_py: Python, _url:&str) -> PyResult<()> {
        //TODO: create soft links in "libs" folder when install
        unimplemented!()
    }

    #[pyfn(m, "uninstall")]
    fn uninstall_capability(_py: Python, _url:&str) -> PyResult<()> {
        unimplemented!()
    }

    #[pyfn(m, "enable")]
    fn enable_capability(_py: Python, _name:&str) -> PyResult<()> {
        unimplemented!()
    }

    #[pyfn(m, "disable")]
    fn disable_capability(_py: Python, _name:&str) -> PyResult<()> {
        unimplemented!()
    }

    #[pyfn(m, "query")]
    fn query_status(_py: Python, _name:&str) -> PyResult<()> {
        unimplemented!()
    }

    #[pyfn(m, "start_daemon")]
    fn start_daemon(_py: Python) -> PyResult<()> {
        let root = Some( String::from("~/.vdm/lib") );
        let server_port = Some(42000);
        let mut daemon = JsonifyIPC::<ShMem>::new(root, server_port);
        daemon.start();
        Ok(())
    }

    Ok(())
}
