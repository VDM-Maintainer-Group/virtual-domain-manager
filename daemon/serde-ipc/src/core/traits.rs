use std::sync::{mpsc,};
//
use crate::core::ffi::ArcFFIManager;

pub trait Serde
// where T: Into<Self::Value> + Clone
{
    type Value: Into<Self::Value> + Clone;
    
    fn to_raw_data(v:&Self::Value) -> Option<String>;
    fn from_raw_data<T>(r:&T) -> Option<Self::Value>
    where T: Into<Self::Value> + Clone;
}

pub trait IPCProtocol: Sync+Send+Clone+'static
{
    type Message: Send;

    fn new(uid:String, ffi:ArcFFIManager) -> Self;
    //
    fn is_alive(&self) -> bool;
    fn spawn_send_thread(&mut self, rx: mpsc::Receiver<Self::Message>);
    fn spawn_recv_thread(&mut self, tx: mpsc::Sender<Self::Message>);
    fn stop(&self);
}