
// export core interface
mod core;
pub use crate::core::traits::{IPCProtocol,};
pub use crate::core::ffi::{MetaFuncMap, FFIDescriptor, FFIManager, ArcFFIManager};

// export default protocols
pub mod protocol;

// export JsonifyIPC implementation
mod jsonify_ipc;
pub use jsonify_ipc::JsonifyIPC;
