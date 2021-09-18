use std::path::PathBuf;
use std::{io, fs};
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
// third-party crates
// use tokio::runtime::Runtime as TokioRuntime;
use serde_json::{self, Value as JsonValue};
// root crates
use crate::core::ipc;
use crate::core::ffi;
use crate::core::traits::{Serde, IPCProtocol};
use crate::core::command::ExecResult;

pub struct JsonifyIPC
{
    // root: PathBuf,
    server_port: u16,
    ffi: ffi::ArcFFIManager,
}

impl Serde for ffi::FFIManager
{
    type Value = JsonValue;

    fn to_raw_data(v:&JsonValue) -> Option<String> {
        serde_json::to_string(v).ok()
    }

    fn from_raw_data<T>(r:&T) -> Option<JsonValue> 
    where T: Into<JsonValue> + Clone
    {
        Some( r.clone().into() )
        // serde_json::from_str(r).ok()
    }
}

impl JsonifyIPC
{
    /// Return JsonifyIPC handle configured with given:
    /// - (Optional) **path**: the working directory for capability, default is `~/.vdm/libs`
    pub fn new(root:Option<String>, server_port:Option<u16>) -> Self {
        let root = root.unwrap_or( "~/.serde_ipc".into() );
        let root = PathBuf::from( shellexpand::tilde(&root).into_owned() );
        let server_port = server_port.unwrap_or(42000);

        let ffi = Arc::new(Mutex::new(
            ffi::FFIManager::new(root)
        ));
        
        JsonifyIPC {
            server_port, ffi
        }
    }

    /// Start the JsonifyIPC daemon waiting for client connection.
    #[tokio::main]
    pub async fn start<P>(&mut self)
    where P: IPCProtocol
    {
        let ffi = self.ffi.clone();
        let server = ipc::IPCServer::<P>::new(
            self.server_port, ffi
        );

        ipc::IPCServer::daemon( server ).await
    }
}

impl JsonifyIPC
{
    /// Add service via FFI Manager
    pub fn install_service(&self, src_path:String) -> ExecResult {
        let directory = PathBuf::from( shellexpand::tilde(&src_path).into_owned() );
        let manifest = fs::File::open( directory.join("manifest.json") )
                        .or( Err(format!("'manifest.json' file not found.")) )?;
        let manifest:JsonValue = serde_json::from_reader( io::BufReader::new(manifest) )
                        .or( Err(format!("manifest file load failed.")) )?;
        
        // 1. check basic information
        let mut metadata = ffi::Metadata {
            name: manifest.get("name").and_then( |val|{val.as_str()} )
                    .ok_or( format!("'name' section missing in manifest file.") )?.into(),
            class: manifest.get("type").and_then( |val|{val.as_str()} )
                    .ok_or( format!("'type' section missing in manifest file.") )?.into(),
            version: manifest.get("version").and_then( |val|{val.as_str()} )
                    .ok_or( format!("'version' section missing in manifest file.") )?.into(),
            func: HashMap::new()
        };
        // 2. check "build" information
        let build: ffi::BuildTemplate = manifest.get("build").and_then(|val|{
                serde_json::from_value( val.clone() ).ok()
        }).ok_or( format!("'build' section missing in manifest file.") )?;
        // 3. check "runtime" information
        let runtime: ffi::RuntimeTemplate = manifest.get("runtime").and_then(|val|{
                serde_json::from_value( val.clone() ).ok()
        }).ok_or( format!("'runtime' section missing in manifest file.") )?;
        // 4. load "metadata" section
        let metafunc: HashMap<String,ffi::MetaFunc> = manifest.get("metadata").and_then(|val|{
                serde_json::from_value( val.clone() ).ok()
        }).ok_or( format!("'metadata' format error.") )?;
        metadata.func.extend(metafunc);

        let _ffi = self.ffi.lock().unwrap();
        _ffi.install(directory, metadata, build, runtime)
    }

    /// Remove service via FFI Manager
    pub fn uninstall_service(&self, name:String) -> ExecResult {
        let _ffi = self.ffi.lock().unwrap();
        _ffi.uninstall(&name)
    }
}

impl JsonifyIPC
{
    /// Get service directly via FFI Manager
    pub fn get_service(&mut self, name:String) -> Option<(String,Option<ffi::MetaFuncMap>)> {
        let mut _ffi = self.ffi.lock().ok()?;
        _ffi.register(&name)
    }

    /// Destroy service directly via FFI Manager
    pub fn put_service(&mut self, name:String, srv_use_sig: String) {
        let mut _ffi = self.ffi.lock().unwrap();
        _ffi.unregister(&name, &srv_use_sig);
    }

    pub fn enable_service(&self, name:String) -> ExecResult {
        let mut _ffi = self.ffi.lock().unwrap();
        _ffi.switch(&name, true)
    }

    pub fn disable_service(&self, name:String) -> ExecResult {
        let mut _ffi = self.ffi.lock().unwrap();
        _ffi.switch(&name, false)
    }

    pub fn service_status(&self, name:String) -> Option<bool> {
        let mut _ffi = self.ffi.lock().unwrap();
        _ffi.report(&name)
    }
}

#[test]
fn register_run_and_unregister() {
    let mut server = JsonifyIPC::new(None, None);
    let src_name = "inotify-lookup";
    let src_path:String = "~/build/vdm-capability-library/inotify-lookup".into();
    server.install_service(src_path).unwrap();
    {
        let (sig, spec) = server.get_service(src_name.into()).unwrap();
        println!("{}, {:?}", sig, spec);
        {
            let args = vec![ serde_json::to_string("code").unwrap() ];
            let descriptor: ffi::FFIDescriptor = (sig.clone(), "register".into(), args);
            let _ffi = server.ffi.lock().unwrap();
            _ffi.execute(descriptor.clone(), move |res|{
                println!("get results: {}",res);
            });
            std::thread::sleep( std::time::Duration::from_millis(100) );
        }
        server.put_service(src_name.into(), sig);
    }
    server.uninstall_service(src_name.into()).unwrap();
}

// A Python Library Test
// fn register_run_and_unregister() {
//     let mut server = JsonifyIPC::new(None, None);
//     let src_path:String = "~/build/demo/python".into();
//     server.install_service(src_path).unwrap();
//     {
//         let (sig, spec) = server.get_service("test".into()).unwrap();
//         println!("{}, {:?}", sig, spec);
//         let (sig1, spec1) = server.get_service("test".into()).unwrap();
//         println!("{}, {:?}", sig1, spec1);
//         assert_eq!(spec1.is_none(), true);
//         {
//             let args = vec![ serde_json::to_string("World").unwrap() ];
//             let descriptor: ffi::FFIDescriptor = (sig.clone(), "main".into(), args);
//             //
//             let _ffi = server.ffi.lock().unwrap();
//             for _ in 0..10 {
//                 _ffi.execute(descriptor.clone(), move |res|{
//                     println!("get results: {}",res);
//                 });
//             }
//             std::thread::sleep( std::time::Duration::from_millis(500) );
//         }
//         server.put_service("test".into(), sig);
//         server.put_service("test".into(), sig1);
//     }
//     server.uninstall_service("test".into()).unwrap();
// }
