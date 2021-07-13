use std::path::{Path, PathBuf};
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

    pub fn run(&self, command:&String) -> Result<(),Option<i32>> {
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

}

impl Commander {
    pub fn build_dependency(&self, args:DepMap) -> ExecResult {
        let mut ret = Ok(());

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

    pub fn build_script(&self, args:Vec<String>) -> ExecResult {
        let mut ret = Ok(());

        for command in args.iter() {
            if let Err(_) = self.run(command) {
                ret = Err( format!("build failed for '{}'", command) );
                break
            }
        }

        ret
    }

    pub fn build_output(&self, args:Vec<String>) -> Option<String> {
        let mut ret = None;

        for (i, val) in args.iter().enumerate() {
            let filename:Vec<&str> = val.split('@').collect();
            let dest_path = {
                match filename.len() {
                    1 => {
                        Some( PathBuf::from(filename[0]) )
                    },
                    2 => {
                        let dest:PathBuf = [self.root.as_path(), Path::new(filename[1])].iter().collect();
                        if let Some(parent) = dest.parent() {
                            if !parent.exists() {
                                fs::create_dir_all(parent).unwrap_or(());
                            }
                            Some( dest )
                        } else { None }
                    },
                    _ => None
                }
            };

            if let Some(dest_path) = dest_path {
                if i==0 { //the first entry is main entry
                    ret = Some( String::from(filename[1]) );
                }
                let _command = format!("cp -rf {} {}", filename[0], dest_path.display());
                if let Err(_) = self.run(&_command) {
                    ret = None;
                    break
                }
            }
            else {
                ret = None;
                break
            }
        }

        ret
    }

    pub fn runtime_dependency(&self, args:DepMap) -> ExecResult {
        self.build_dependency(args)
    }

    //runtime-status: String
    

    //runtime-enable: Vec<String>

    //runtime-disable: Vec<String>
}
