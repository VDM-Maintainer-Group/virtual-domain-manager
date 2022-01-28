use std::path::PathBuf;
// use std::{thread, time};
use std::sync::{Arc, Mutex};
use std::collections::{HashMap, BTreeMap, BTreeSet};
//
use confy;
use rand::{self, Rng};
use serde::{Serialize,Deserialize};
use threadpool::ThreadPool;
use pyo3::{prelude::*, types::*};
//
// use crate::core::traits::Serde;
use crate::core::command::*;
use crate::core::service::*;

pub type ArcFFIManager = Arc<Mutex<FFIManager>>;
pub type FFIDescriptor = (String, String, String);
pub type DepMap = HashMap<String, Vec<String>>;
pub type MetaFuncMap = HashMap<String, MetaFunc>;

#[derive(Serialize, Deserialize)]
pub struct BuildTemplate {
    dependency: Option<DepMap>,
    script: Option<Vec<String>>,
    output: Vec<String>
}

#[derive(Default, Serialize, Deserialize, Debug)]
pub struct RuntimeTemplate {
    dependency: Option<DepMap>,
    status: String,
    enable: Vec<String>,
    disable: Vec<String>
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct MetaFunc {
    pub restype: String,
    pub args: Vec<HashMap<String, String>>
}

#[derive(Default, Serialize, Deserialize, Debug)]
pub struct Metadata {
    pub name: String,
    pub class: String,
    pub version: String,
    pub func: HashMap<String, MetaFunc>
}

#[derive(Default, Serialize, Deserialize, Debug)]
struct ServiceConfig {
    entry: String,
    files: Vec<String>,
    metadata: Metadata,
    runtime: RuntimeTemplate
}

//================================================================================//

type ServiceSig = u32;
type UsageSig   = u32;
type ServiceMap = BTreeMap<String, ServiceSig>;
type UsageMap   = BTreeMap<ServiceSig, BTreeSet<UsageSig>>;

pub struct FFIManager {
    root: PathBuf,
    services: BTreeMap<ServiceSig, Arc<Service>>,
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
        { // change working directory (panic as you like)
            std::fs::create_dir_all(&root).unwrap();
            std::env::set_current_dir(&root).unwrap(); 
        }
        {
            let root = root.canonicalize().unwrap();
            Python::with_gil(|py| {
                let sys = py.import("sys").unwrap();
                let path:&PyList = PyTryInto::try_into(&*sys.getattr("path").unwrap()).unwrap();
                path.insert(0, &root).unwrap();
            });
        }
        FFIManager{ root, services, service_map, usage_map, pool }
    }

    fn write_config_file(&self, cfg: ServiceConfig) -> ExecResult {
        let name = String::from( &cfg.metadata.name );
        let service_path = self.root.join( &name );
        let cfg_name = format!("{}.conf", "");
        std::fs::create_dir_all(&service_path).unwrap_or(());
        match confy::store_path(&service_path.join(cfg_name), cfg) {
            Ok(_) => Ok(()),
            Err(_) => {
                Err( format!("Config file store failed for service '{}'.", name) )
            }
        }
    }

    fn load_config_file(&self, name:&String) -> Option<ServiceConfig> {
        let cfg_file = self.root.join(&name).join(".conf");
        if cfg_file.exists() {
            confy::load_path(&cfg_file).ok().and_then(|cfg:ServiceConfig|{
                if !cfg.entry.is_empty() {
                    Some(cfg)
                } else { None }
            })
        }
        else { None }
    }

    fn prepare_runtime(&self, files:Vec<String>, metadata:Metadata, runtime:RuntimeTemplate) -> ExecResult
    {
        let commander = Commander::new(self.root.clone(), self.root.clone());
        let results = || -> ExecResult {
            commander.runtime_dependency( runtime.dependency.clone() )?;
            commander.runtime_enable( &runtime.enable )?;
            Ok(())
        };

        match results() {
            Ok(_) => {
                let cfg = ServiceConfig{
                    entry: String::from(&files[0]), files,
                    metadata:metadata, runtime:runtime
                };
                self.write_config_file(cfg)?;
                Ok(())
            },
            Err(msg) => {
                commander.remove_output(&metadata.name, &files);
                Err(msg)
            }
        }
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

        self.service_map.insert( name.into(), service_sig );
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

    fn insert_service(&mut self, cfg: ServiceConfig) -> Option<ServiceSig> {
        // assert_eq!( self.service_map.get(&cfg.metadata.name), None );

        // 1. load service
        let name = String::from( &cfg.metadata.name );
        let service = Arc::new( Service::load( &cfg.entry, cfg.metadata )? );
        // 2. allocate service signature
        let srv_sig = self.insert_service_map(&name).unwrap(); //"None" is always impossible
        self.services.insert(srv_sig, service);
        // 3. initialize usage map
        self.usage_map.insert(srv_sig, BTreeSet::new());
        
        Some(srv_sig)
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

// service install / uninstall / report / switch
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
                Err( format!("No output files specified.") )
            }
        }
    }

    pub fn uninstall(&self, name:&String) -> ExecResult {
        let commander = Commander::new(self.root.clone(), self.root.clone());
        if let Some(cfg) = self.load_config_file(name) {
            commander.runtime_disable(&cfg.runtime.disable).unwrap_or(()); //ignore the error
            commander.remove_output(&cfg.metadata.name, &cfg.files);
            Ok(())
        } else {
            Err( format!("Service '{}' not found.", name) )
        }
    }

    pub fn report(&self, name:&String) -> Option<bool> {
        let command = Commander::new(self.root.clone(), self.root.clone());
        let cfg = self.load_config_file(name)?;
        command.runtime_status( &cfg.runtime.status )
    }

    pub fn switch(&self, name:&String, enable:bool) -> ExecResult {
        let command = Commander::new(self.root.clone(), self.root.clone());
        let cfg = self.load_config_file(name)
                .ok_or( format!("failed to load config file.") )?;
        match enable {
            true => command.runtime_enable( &cfg.runtime.enable ),
            false => command.runtime_disable( &cfg.runtime.disable )
        }
    }
}

// service register / unregister
impl FFIManager {
    pub fn register(&mut self, name: &String) -> Option<(String,Option<MetaFuncMap>)> {
        let cfg = self.load_config_file(name)?;
        let spec = cfg.metadata.func.clone();

        let (service_sig, spec) = {
            match self.service_map.get(name) {
                Some(sig) => {
                    Some( (*sig, Some(spec)) )
                },
                None => { //load service here
                    match self.insert_service(cfg) {
                        Some(srv_sig) => Some( (srv_sig, Some(spec)) ),
                        None => None
                    }
                }
            }
        }?;
        let usage_sig = self.insert_usage_map(&service_sig)?; //"None" is always impossible
        let srv_use_sig:u64 = ((service_sig as u64) << 32) + (usage_sig as u64);
        Some( (srv_use_sig.to_string(),spec) )
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
    pub fn get_service_by_sig(&self, srv_use_sig: &String) -> Option<Arc<Service>> {
        let srv_use_sig:u64 = srv_use_sig.parse().unwrap_or(0);
        let service_sig = (srv_use_sig >> 32) as u32;   //high u32
        let usage_sig   = srv_use_sig as u32;           //low u32

        let srv_usage = self.usage_map.get(&service_sig)?;
        if srv_usage.contains(&usage_sig) {
            Some(Arc::clone(
                self.services.get(&service_sig)?
            ))
        } else { None }
    }

    pub fn execute<CB>(&self, descriptor:FFIDescriptor, callback:CB)
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
    
    //TODO: NOT DEBUGGED.
    pub fn chain_execute<CB>(&self, _descriptors:Vec<FFIDescriptor>, _callback:CB)
    where CB: FnOnce(String) -> () + Send + 'static
    {
        unimplemented!()
        // let shared_results:Vec<Option<String>> = vec![None; descriptors.len()];
        // let shared_results = Arc::new(Mutex::new( shared_results ));
        // let sig_func_map:Vec<_> = descriptors.iter().map(|(sig, func, _)| {
        //     format!("restype_{}_{}", sig, func)
        // }).collect();

        // for (i, (sig, func, mut args)) in descriptors.into_iter().enumerate() {
        //     let shared_results = shared_results.clone();
        //     let service = self.get_service_by_sig(&sig);
        //     let mut dep_map:Vec<_> = args.iter().enumerate().filter_map(|(pos, arg)| {
        //         if arg.starts_with("restype") {
        //             let idx = sig_func_map.iter().position( |x|{x==arg} )?;
        //             Some( (pos, idx) )
        //         } else { None }
        //     }).collect();

        //     self.pool.execute(move || loop {
        //         let dep_map:Vec<_> = dep_map.drain(..).filter(|(pos,idx)|{
        //             if let Ok(_results) = shared_results.lock() {
        //                 if let Some(ref res) = _results[*idx] {
        //                     args[*pos] = res.clone();
        //                     return false
        //                 }
        //             }
        //             true
        //         }).collect();

        //         if dep_map.is_empty() {
        //             let result = {
        //                 if let Some(ref service) = service {
        //                     service.call(&func, args)
        //                 } else { None }
        //             }.unwrap_or( String::new() );
        //             let mut _results = shared_results.lock().unwrap(); //panic as you like
        //             _results[i] = Some( result );
        //             break;
        //         } else { thread::sleep(time::Duration::from_millis(10)); }
        //     });
        // }

        // // create callback check thread
        // let shared_results = shared_results.clone();
        // self.pool.execute(move || loop {
        //     if let Ok(_results) = shared_results.lock() {
        //         if _results.iter().all( |x|{x.is_some()} ) {
        //             let res = _results.last().unwrap().clone().unwrap();
        //             callback(res);
        //             break
        //         }
        //     }
        //     thread::sleep(time::Duration::from_millis(10));
        // });
    }
}
