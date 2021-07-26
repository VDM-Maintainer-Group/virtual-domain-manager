use std::sync::{mpsc, Arc, Mutex};
use std::ffi::CString;
use std::convert::TryFrom;
use std::collections::HashMap;
//
use num_enum::TryFromPrimitive;
use shared_memory::{ShmemConf};
use serde::{Serialize,Deserialize};
use threadpool::ThreadPool;
//
use serde_ipc::{MetaFuncMap, FFIDescriptor, ArcFFIManager};
use serde_ipc::IPCProtocol;

type Message = (u32, String);

// const SHM_REQ_MAX_SIZE:usize = 10*1024; //10KB
const SHM_RES_MAX_SIZE:usize = 1024*1024; //1MB

#[allow(non_camel_case_types)]
#[derive(Debug, Eq, PartialEq, TryFromPrimitive)]
#[repr(u16)]
enum Command {
    ALIVE       = 0x00,
    REGISTER    = 0x01,
    UNREGISTER  = 0x02,
    CALL        = 0x03,
    ONE_WAY     = 0x04,
    CHAIN_CALL  = 0x05
}

#[repr(C,packed)]
#[derive(Debug, Copy, Clone)]
struct ReqHeader {
    seq: u32,
    command: u16,
    size: u16
}

#[repr(C,packed)]
#[derive(Debug, Copy, Clone)]
struct ResHeader {
    seq: u32,
    size: u32
}

const REQ_HEADER_LEN:usize = std::mem::size_of::<ReqHeader>();
const RES_HEADER_LEN:usize = std::mem::size_of::<ResHeader>();

#[derive(Serialize,Deserialize)]
struct NameCall {
    name: String
}

#[derive(Serialize,Deserialize)]
struct NameCallRes {
    sig: String,
    spec: Option<MetaFuncMap>
}

#[derive(Serialize,Deserialize)]
struct FuncCall {
    sig: String,
    func: String,
    args: Vec<String>
}

#[derive(Serialize,Deserialize)]
struct ChainCall {
    sig_func_args_table: Vec<FuncCall>
}

unsafe fn any_as_u8_slice<T: Sized>(p: &T) -> &[u8] {
    ::std::slice::from_raw_parts(
        (p as *const T) as *const u8,
        ::std::mem::size_of::<T>(),
    )
}

fn set_mask(seq:&mut u8) {
    *seq |= 0x80;
}
fn unset_mask(seq:&mut u8) {
    *seq &= 0x7F;
}
fn test_mask(seq:&u8) -> bool {
    seq & 0x80 == 1
}

fn acquire_lock(sem: *mut libc::sem_t, shm_name:&String, write_flag:bool) -> Result<(), String>
{
    loop {
        if unsafe{ libc::sem_wait(sem) } != 0 {
            break Err( format!("Semaphore: acquire lock failed.") )
        }
        let mut shm = ShmemConf::new().os_id(&shm_name).open().map_err(|_|{
            format!("SharedMemory: open failed during acquire lock.")
        })?;
        unsafe{
            let shm_slice = shm.as_slice_mut();
            if test_mask(&shm_slice[0])!=write_flag {
                if libc::sem_post(sem) != 0 {
                    break Err( format!("Semaphore: acquire lock failed.") )
                }
                std::thread::yield_now();
                continue
            }
        }
        break Ok(())
    }
}

fn release_lock(sem: *mut libc::sem_t, shm_name:&String, write_flag:bool) -> Result<(), String> {
    let mut shm = ShmemConf::new().os_id(&shm_name).open().map_err(|_|{
        format!("SharedMemory: open failed during release lock.")
    })?;
    unsafe{
        let shm_slice = shm.as_slice_mut();
        if write_flag {
            set_mask(&mut shm_slice[0]);
        }
        else {
            unset_mask(&mut shm_slice[0]);
        }
    };
    if unsafe{ libc::sem_post(sem) } < 0 {
        Err( format!("Semaphore: release lock failed.") )
    } else { Ok(()) }
}

fn _recv_loop(ffi: ArcFFIManager, tx: mpsc::Sender<Message>, req_id: String) {
    let acquire_read_lock = |sem, shm_name|{ acquire_lock(sem, shm_name, false) };
    let release_read_lock = |sem, shm_name|{ release_lock(sem, shm_name, false) };
    //
    let sem_name = CString::new( req_id.clone() ).unwrap();
    let sem_req = match unsafe { libc::sem_open(sem_name.as_ptr(), 0, 0o600, 0) } {
        i if i != libc::SEM_FAILED => Ok(i),
        _ => Err( format!("sem open failed.") )
    }.unwrap(); //panic as you like
    let mut register_records = HashMap::<String, String>::new();

    let mut loop_result = || -> Result<(), Box<dyn std::error::Error>> {
        loop {
            acquire_read_lock(sem_req, &req_id)?;
                let shm_req = ShmemConf::new().os_id(&req_id).open()?;
                let shm_slice = unsafe{ shm_req.as_slice() };
                let req_header:ReqHeader = unsafe{
                    let _header:Vec<u8> = shm_slice[..REQ_HEADER_LEN].iter().cloned().collect();
                    println!("res_header: {:?}", _header); //FIXME: remove it
                    std::ptr::read( _header.as_ptr() as *const _ )
                };
                let req_data = {
                    let _length = REQ_HEADER_LEN + req_header.size as usize;
                    let _data = shm_slice[REQ_HEADER_LEN.._length].iter().cloned().collect();
                    String::from_utf8(_data)?
                };
            release_read_lock(sem_req, &req_id)?;

            // match command with its response
            let command = Command::try_from(req_header.command)?;
            match command {
                Command::ALIVE => { //synchronized call
                    tx.send( (req_header.seq, String::new()) )?;
                },
                Command::REGISTER => { //synchronized call
                    let args: NameCall = serde_json::from_str(&req_data)?;
                    let mut ffi_obj = ffi.lock()?;
                    if let Some((sig, spec)) = ffi_obj.register(&args.name) {
                        register_records.insert( args.name, sig.clone() );
                        let res = serde_json::to_string(&NameCallRes{sig,spec})?;
                        tx.send( (req_header.seq, res) )?;
                    }
                },
                Command::UNREGISTER => { //synchronized call
                    let args: NameCall = serde_json::from_str(&req_data)?;
                    let mut ffi_obj = ffi.lock()?;
                    if let Some(sig) = register_records.get(&args.name) {
                        ffi_obj.unregister( &args.name, sig );
                        register_records.remove(&args.name);
                    }
                },
                Command::CALL => {
                    let tx_ref = tx.clone();
                    let args: FuncCall = serde_json::from_str(&req_data)?;
                    let desc: FFIDescriptor = (args.sig, args.func, args.args);
                    let ffi_obj = ffi.lock()?;
                    ffi_obj.execute(desc, move |res|{
                        tx_ref.send( (req_header.seq, res) ).unwrap_or(());
                    });                    
                },
                Command::ONE_WAY => {
                    let args: FuncCall = serde_json::from_str(&req_data)?;
                    let desc: FFIDescriptor = (args.sig, args.func, args.args);
                    let ffi_obj = ffi.lock()?;
                    ffi_obj.execute(desc, |_|{}); //no callback for one-way
                },
                Command::CHAIN_CALL => {
                    let tx_ref = tx.clone();
                    let args: ChainCall = serde_json::from_str(&req_data)?;
                    let descs: Vec<FFIDescriptor> = args.sig_func_args_table.into_iter().map(|args| {
                        (args.sig, args.func, args.args)
                    }).collect();
                    let ffi_obj = ffi.lock()?;
                    ffi_obj.chain_execute(descs, move |res|{
                        tx_ref.send( (req_header.seq, res) ).unwrap_or(());
                    });
                }
            }
        }
    };
    
    // finalization after connection drop
    if let Err(e) = loop_result() {
        eprintln!("Recv Loop Error: {}", e);
    }
    if let Ok(mut ffi_obj) = ffi.lock() {
        register_records.iter().for_each(|(k,v)|{
            ffi_obj.unregister(k, v);
        })
    }
    _close(sem_name, sem_req);
}

fn _send_loop(rx: mpsc::Receiver<Message>, res_id: String) {
    let acquire_write_lock = |sem, shm_name|{ acquire_lock(sem, shm_name, true) };
    let release_write_lock = |sem, shm_name|{ release_lock(sem, shm_name, true) };
    //
    let mut shm_res = match ShmemConf::new().size(SHM_RES_MAX_SIZE).os_id( &res_id ).create() {
        Ok(m) => m,
        Err(e) => {
            eprintln!("Unable to create or open shmem os_id: {}", e);
            return;
        }
    };
    shm_res.set_owner(true);
    let sem_name = CString::new( res_id.clone() ).unwrap();
    let sem_res = match unsafe { libc::sem_open(sem_name.as_ptr(), libc::O_CREAT|libc::O_EXCL, 0o600, 0) } {
        i if i != libc::SEM_FAILED => Ok(i),
        _ => Err( format!("sem open failed.") )
    }.unwrap(); //panic as you like

    let loop_result = || -> Result<(), Box<dyn std::error::Error>> {
        // ready to write
        if unsafe{ libc::sem_post(sem_res) } < 0 {
            return Ok(());
        }
        while let Ok(message) = rx.recv() {
            let mut shm_res = ShmemConf::new().os_id(&res_id).open()?;
            // format the message
            let (seq, data) = message;
            let data = data.as_bytes();
            let size = data.len() as u32;
            let _header = ResHeader{ seq, size };
            println!("res_header: {:?}", _header); //FIXME: remove it

            acquire_write_lock(sem_res, &res_id)?;
            unsafe {
                let shm_slice = shm_res.as_slice_mut();
                let res_header = any_as_u8_slice(&_header);
                let _length = RES_HEADER_LEN + size as usize;
                shm_slice[..RES_HEADER_LEN].clone_from_slice(&res_header);
                shm_slice[RES_HEADER_LEN.._length].clone_from_slice(&data);
            }
            release_write_lock(sem_res, &res_id)?;
        }
        Ok(())
    };
    
    // finalization after connection drop
    if let Err(e) = loop_result() {
        eprintln!("Send Loop Error: {}", e);
    }
    _close(sem_name, sem_res);
}

fn _close(sem_name:CString, sem :*mut libc::sem_t) {
    unsafe{
        libc::sem_close(sem);
        libc::sem_unlink(sem_name.as_ptr());
    };
}

pub struct ShMem {
    uid: String,
    ffi: Option<ArcFFIManager>,
    pool: Arc<Mutex<ThreadPool>>
}

impl IPCProtocol for ShMem {
    type Message = (u32, String);

    fn new(uid:String, ffi:ArcFFIManager) -> Self {
        let ffi = Some(ffi);
        let pool = Arc::new(Mutex::new(
            ThreadPool::new(2)
        ));
        Self{ uid, ffi, pool }
    }

    fn is_alive(&self) -> bool {
        if let Ok(pool_obj) = self.pool.lock() {
            pool_obj.active_count() < 2
        }
        else {
            false
        }
    }

    fn stop(&self) {
        //stop when the pool is dropped.
    }

    fn spawn_send_thread(&mut self, rx: mpsc::Receiver<Self::Message>) {
        use std::{thread, time};
        let res_id = format!("{}_res", self.uid);
        
        if let Ok(pool_obj) = self.pool.lock() {
            pool_obj.execute(move || {
                _send_loop(rx, res_id);
            });
            thread::sleep( time::Duration::from_millis(10) ); //promise thread starts
        }
    }

    fn spawn_recv_thread(&mut self, tx: mpsc::Sender<Self::Message>) {
        let ffi = Arc::clone( self.ffi.as_ref().unwrap() ); //panic as you like
        let req_id = format!("{}_req", self.uid);
        
        if let Ok(pool_obj) = self.pool.lock() {
            pool_obj.execute(move || {
                _recv_loop(ffi, tx, req_id);
            });
        }
    }

}
