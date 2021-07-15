mod core;

// export core interface
pub use crate::core::traits::{IPCProtocol,};
pub use crate::core::ffi::{FFIManager, ArcFFIManager};

// export JsonifyIPC implementation
mod jsonify_ipc;
pub use jsonify_ipc::JsonifyIPC;
