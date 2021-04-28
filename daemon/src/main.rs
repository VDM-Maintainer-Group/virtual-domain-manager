
mod ipc_daemon {
    // - RPC server response to async event
    //      - "connect/disconnect" from client
    //      - "register/unregister" from client (with error)
    //      - "call/one-way-call/chain-call" from client (with error)
    //      - execute asynchronously and stateless in separated thread
    // - On-demand load cdll library with "usage count"
    //      - load from "~/.vdm/capability" using "ffi.rs"
    //      - with "register" command, +1; with "unregister" command, -1
    //      - zero for release
}

fn main() {
    // call on ipc_daemon with async event
}