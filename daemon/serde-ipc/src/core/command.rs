use std::path::{PathBuf};
use std::process::Command;
use std::fs;
use std::collections::HashMap;

pub type DepMap = HashMap<String, Vec<String>>;
pub type ExecResult = Result<(), String>;

pub struct Commander {
    root: PathBuf,
    work: PathBuf
}

impl Commander {
    pub fn new(root:PathBuf, work:PathBuf) -> Self {
        Self{ root, work }
    }

    fn run(&self, command:&String) -> Result<(),Option<i32>> {
        let result = Command::new("bash")
                    .current_dir( self.work.clone() )
                    .args(&["-c", &command])
                    .status();
        match result {
            Err(_) => Err(None),
            Ok(status) => {
                if status.success() {
                    Ok(())
                }
                else {
                    Err(status.code())
                }
            }
        }
    }

    fn run_prog(&self, prog: &str, args:Vec<&str>) -> Result<String, ()> {
        let result = Command::new(prog)
                    .current_dir( self.root.clone() )
                    .args(args)
                    .output();
        match result {
            Err(_) => Err(()),
            Ok(output) => {
                Ok( String::from_utf8_lossy(&output.stdout).into_owned() )
            }
        }
    }
}

impl Commander {
    pub fn build_dependency(&self, args:Option<DepMap>) -> ExecResult {
        let mut ret = Ok(());
        let args = match args {
            Some(args) => args,
            None => return Ok(())
        };

        for (key, values) in args.iter() {
            match key.as_ref() {
                "pip" => {
                    for v in values.iter() {
                        if let Err(_) = self.run( &format!("pip install {}", v) ) {
                            ret = Err( format!("pip install failed for '{}'", v) );
                            break
                        }
                    }
                },
                "cargo" => {
                    for v in values.iter() {
                        if let Err(_) = self.run( &format!("cargo install {}", v) ) {
                            ret = Err( format!("cargo install failed for '{}'", v) );
                            break
                        }
                    }
                },
                command => {
                    ret = Err( format!("Unsupported command: {}", command) );
                    break
                }
            }
            if let Err(_) = ret {
                break
            }
        }

        ret
    }

    pub fn build_script(&self, args:Option<Vec<String>>) -> ExecResult {
        let mut ret = Ok(());
        let args = match args {
            Some(args) => args,
            None => return Ok(())
        };

        for command in args.iter() {
            if let Err(_) = self.run(command) {
                ret = Err( format!("build failed for '{}'", command) );
                break
            }
        }

        ret
    }

    pub fn build_output(&self, args:Vec<String>) -> Option<Vec<String>> {
        // collection of Option<String> --> Option<Vec<String>>
        args.iter().map(|arg| {
            let output_file:Vec<&str> = arg.trim().split('@').collect();
            match output_file.len() {
                1 => Some( output_file[0] ),
                2 => Some( output_file[1] ),
                _ => None
            }.and_then(|dest_file|{
                let src_path = self.work.join(output_file[0]);
                let dst_path = self.root.join(dest_file);
                //
                if src_path.exists() && src_path != self.work {
                    fs::create_dir_all( dst_path.parent()? ).ok()?;
                    let cmd = format!("cp -rf {} {}", src_path.display(), dst_path.display());
                    self.run(&cmd).ok()?;
                    Some( dest_file.to_string() )
                } else { None }
            })
        }).collect()
    }

    pub fn remove_output(&self, name:&String, files:&Vec<String>) {
        for filename in files.iter() {
            let _file = self.root.join(filename);
            fs::remove_file(_file).unwrap_or(());
        }
        fs::remove_dir_all( self.root.join(name) ).unwrap_or(());
    }

    pub fn runtime_dependency(&self, args:Option<DepMap>) -> ExecResult {
        self.build_dependency(args)
    }

    pub fn runtime_status(&self, arg:&String) -> Option<bool> {
        if arg.is_empty() {
            return None;
        }
        else {
            let mut args:Vec<&str> = arg.split(' ').collect();
            let params:Vec<&str> = args.drain(1..).collect();
            match self.run_prog(args[0], params) {
                Ok(_) => Some(true),
                Err(_) => Some(false)
            }
        }
    }

    pub fn runtime_enable(&self, args:&Vec<String>) -> ExecResult {
        let mut ret = Ok(());

        for arg in args.iter() {
            match self.runtime_status(arg) {
                Some(true) => {},
                Some(false) | None => {
                    ret = Err( format!("Enable failed for '{}'", arg) );
                    break
                }
            }
        }

        ret
    }

    pub fn runtime_disable(&self, args:&Vec<String>) -> ExecResult {
        self.runtime_enable(args)
    }
}
