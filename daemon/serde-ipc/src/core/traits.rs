use std::sync::{mpsc,};
//
use crate::core::ffi::ArcFFIManagerStub;

pub trait Serde {}

pub trait IPCProtocol: Sync+Send+Clone+'static
{
    type Message: Send;

    fn new(uid:String, ffi:ArcFFIManagerStub) -> Self;
    fn spawn_send_thread(&self, rx: mpsc::Receiver<Self::Message>);
    fn spawn_recv_thread(&self, tx: mpsc::Sender<Self::Message>);
}