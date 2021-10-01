use std::sync::mpsc;
use crate::core::traits::IPCProtocol;
use crate::core::ffi::ArcFFIManager;

pub struct DummyProtocol;
impl IPCProtocol for DummyProtocol {
    type Message = String;

    fn new(_uid:String, _ffi:ArcFFIManager) -> Self {
        DummyProtocol{}
    }
    fn is_alive(&self) -> bool {return true;}
    fn spawn_send_thread(&mut self, _rx: mpsc::Receiver<Self::Message>) {}
    fn spawn_recv_thread(&mut self, _tx: mpsc::Sender<Self::Message>) {}
    fn stop(&self) {}
}

pub mod shmem;