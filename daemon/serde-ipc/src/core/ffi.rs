use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::collections::{HashMap, BTreeMap, BTreeSet};
//
use confy;
use rand::{self, Rng};
use serde::{Serialize,Deserialize};
use threadpool::ThreadPool;
//
// use crate::core::traits::Serde;
use crate::core::command::*;
use crate::core::service::*;

pub type ArcFFIManager = Arc<Mutex<FFIManager>>;
pub type FFIDescriptor = (String, String, Vec<String>);

#[derive(Serialize, Deserialize)]
pub struct BuildTemplate {
    dependency: DepMap,
    script: Vec<String>,
    output: Vec<String>
}

#[derive(Serialize, Deserialize)]
pub struct RuntimeTemplate {
    dependency: DepMap,
    status: String,
    enable: Vec<String>,
    disable: Vec<String>
}

#[derive(Serialize, Deserialize)]
pub struct MetaFunc {
    pub restype: String,
    pub args: Vec<(String, String)>
}

#[derive(Serialize, Deserialize)]
pub struct Metadata {
    name: String,
    pub class: String,
    version: String,
    pub func: HashMap<String, MetaFunc>
}

#[derive(Serialize, Deserialize)]
struct ServiceConfig {
    entry: String,
    files: Vec<String>,
    metadata: Option<Metadata>,
    runtime: Option<RuntimeTemplate>
}

impl Default for ServiceConfig {
    fn default() -> Self {
        Self{
            entry: String::new(), files: Vec::new(),
            metadata: None, runtime: None
        }
    }
}

//================================================================================//

type ServiceSig = u32;
type UsageSig   = u32;
type ServiceMap = BTreeMap<String, ServiceSig>;
type UsageMap   = BTreeMap<ServiceSig, BTreeSet<UsageSig>>;

pub struct FFIManager {
    root: PathBuf,
    services: BTreeMap<ServiceSig, Service>,
    service_map: ServiceMap,
    usage_map: UsageMap,
    pool: ThreadPool
}

// internal basic functions
impl FFIManager {
    pub fn new(root: PathBuf) -> Self {
        let services = BTreeMap::new();
        let service_map = BTreeMap::new();
        let usage_map   = BTreeMap::new();
        let pool = ThreadPool::new(num_cpus::get());
        std::env::set_current_dir(&root).unwrap(); //panic as you like
        FFIManager{ root, services, service_map, usage_map, pool }
    }

    fn write_config_file(&self, cfg: ServiceConfig) -> ExecResult {
        let name = {
            if let Some(ref metadata) = cfg.metadata {
                PathBuf::from(&metadata.name)
            } else { PathBuf::new() }
        };
        let service_path:PathBuf =
                [&self.root, &name].iter().collect();
        std::fs::create_dir_all(&service_path).unwrap_or(());
        match confy::store_path(&service_path, cfg) {
            Ok(_) => Ok(()),
            Err(_) => Err( format!("Config file store failed for service '{}'.", name.display()) )
        }
    }

    fn load_config_file(&self, name:&String) -> Option<ServiceConfig> {
        let name = PathBuf::from(name);
        let service_path:PathBuf =
                [&self.root, &name].iter().collect();
        match confy::load_path(&service_path) {
            Ok(cfg) => Some(cfg),
            Err(_) => None
        }
    }

    fn prepare_runtime(&self, files:Vec<String>, metadata:Metadata, runtime:RuntimeTemplate) -> ExecResult
    {
        let commander = Commander::new(self.root.clone(), self.root.clone());
        commander.runtime_dependency( runtime.dependency.clone() )?;
        //
        let cfg = ServiceConfig{
            entry: String::from(&files[0]), files,
            metadata:Some(metadata), runtime:Some(runtime)
        };
        self.write_config_file(cfg)?;
        Ok(())
    }
}

// internal load / unload functions
impl FFIManager {
    fn gen_sig() -> u32 {
        // thread_rng().sample_iter(&Alphanumeric).take(16).map(char::from).collect()
        rand::thread_rng().gen()
    }

    fn insert_service_map(&mut self, name: &String) -> Option<ServiceSig> {
        let service_sig = loop { //dead loop
            let sig = Self::gen_sig();
            if !self.usage_map.contains_key(&sig) {
                break sig
            }
        };

        self.service_map.insert( name.into(), service_sig )?;
        Some( service_sig )
    }

    fn insert_usage_map(&mut self, service_sig: &ServiceSig) -> Option<UsageSig> {
        let srv_usage = self.usage_map.get_mut(service_sig)?;
        let usage_sig = loop { //dead loop
            let sig = Self::gen_sig();
            if !srv_usage.contains(&sig) {
                break sig
            }
        };

        srv_usage.insert( usage_sig );
        Some( usage_sig )
    }

    fn insert_service(&mut self, sig:ServiceSig, cfg: ServiceConfig) -> Option<()> {
        let service = Service::load( &cfg.entry, cfg.metadata.unwrap() )?;
        self.services.insert(sig, service);
        Some(())
    }

    fn cleanup(&mut self, srv_name:&String, srv_sig:&ServiceSig) {
        if let Some(srv_usage) = self.usage_map.get(srv_sig) {
            if srv_usage.is_empty() {
                self.usage_map.remove(srv_sig);
                self.service_map.remove(srv_name);
                self.services.remove(srv_sig);
            }
        }
    }
}

// service install / uninstall
impl FFIManager {
    pub fn install(&self, directory:PathBuf, 
        metadata:Metadata, build:BuildTemplate, runtime:RuntimeTemplate) -> ExecResult 
    {
        let commander = Commander::new(self.root.clone(), directory);
        commander.build_dependency(build.dependency)?;
        commander.build_script(build.script)?;
        match commander.build_output(build.output) {
            Some(files) => {
                self.prepare_runtime(files, metadata, runtime)?;
                Ok(())
            },
            None => {
                Err( String::from("Installation failed.") )
            }
        }
    }

    pub fn uninstall(&self, name:&String) -> ExecResult {
        let command = Commander::new(self.root.clone(), self.root.clone());
        if let Some(cfg) = self.load_config_file(name) {
            if let Some(ref runtime) = cfg.runtime {
                command.runtime_disable(&runtime.disable)?;
            }
            if let Some(ref metadata) = cfg.metadata {
                let name = &metadata.name;
                command.remove_output(name, &cfg.files);
            }
        }
        Ok(())
    }
}

// service register / unregister
impl FFIManager {
    pub fn register(&mut self, name: &String) -> Option<String> {
        let service_sig = {
            if let Some(sig) = self.service_map.get(name) {
                Some(*sig)
            }
            else {
                let cfg = self.load_config_file(name)?;
                let srv_sig = self.insert_service_map(name)?; //"None" is always impossible
                // try insert service; cleanup if failed.
                if let Some(_) = self.insert_service(srv_sig, cfg) {
                    Some(srv_sig)
                }
                else {
                    self.cleanup(name, &srv_sig);
                    None
                }
            }
        }?;

        let usage_sig = self.insert_usage_map(&service_sig)?; //"None" is always impossible
        let srv_use_sig:u64 = ((service_sig as u64) << 32) + (usage_sig as u64);
        Some( srv_use_sig.to_string() )
    }
    
    pub fn unregister(&mut self, name:&String, srv_use_sig: &String) {
        let srv_use_sig:u64 = srv_use_sig.parse().unwrap_or(0);
        let service_sig = (srv_use_sig >> 32) as u32;   //high u32
        let usage_sig   = srv_use_sig as u32;           //low u32
        
        if let Some(sig) = self.service_map.get(name) {
            if *sig==service_sig {
                if let Some(srv_usage) = self.usage_map.get_mut(&service_sig) {
                    srv_usage.remove(&usage_sig);
                }
                // cleanup if all usages gone
                self.cleanup(name, &service_sig);
            }
        }
    }
}

// service execute / chain_execute
impl FFIManager
{
    fn get_service_by_sig(&self, srv_use_sig: &String) -> Option<&Service> {
        let srv_use_sig:u64 = srv_use_sig.parse().unwrap_or(0);
        let service_sig = (srv_use_sig >> 32) as u32;   //high u32
        let usage_sig   = srv_use_sig as u32;           //low u32

        let srv_usage = self.usage_map.get(&service_sig)?;
        if srv_usage.contains(&usage_sig) {
            self.services.get(&service_sig)
        } else { None }
    }

    pub fn execute<CB>(&'static self, descriptor:FFIDescriptor, callback:CB)
    where CB: FnOnce(String) -> () + Send + 'static,
    {
        let (sig, func, args) = descriptor;
        let service = self.get_service_by_sig(&sig);

        self.pool.execute(move || {
            let result = {
                if let Some(service) = service {
                    service.call(&func, args)
                } else { None }
            }.unwrap_or( String::new() );
            callback(result);
        });
    }
    
    pub fn chain_execute<CB>(&self, descriptors:Vec<FFIDescriptor>, callback:CB)
    where CB: FnOnce(String) -> () + Send + 'static
    {
        unimplemented!()
    }
}