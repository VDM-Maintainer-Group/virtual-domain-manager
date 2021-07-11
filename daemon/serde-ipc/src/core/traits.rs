use std::sync::{mpsc,};
//
use crate::core::ffi::ArcFFIManagerStub;

pub trait Serde {
    type Value;

    fn from_raw_data(&self, r:&str) -> Self::Value;
    fn to_raw_data(&self, v:&Self::Value) -> String;
}

pub trait IPCProtocol: Sync+Send+Clone+'static
{
    type Message: Send;

    fn new(uid:String, ffi:ArcFFIManagerStub) -> Self;
    //
    fn is_alive(&self) -> bool;
    fn spawn_send_thread(&mut self, rx: mpsc::Receiver<Self::Message>);
    fn spawn_recv_thread(&mut self, tx: mpsc::Sender<Self::Message>);
    fn stop(&self);
}