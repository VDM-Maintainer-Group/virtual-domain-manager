# Vritual Domain Manager

Virtual Domain Manager is for fast virtual workspace setup, archieve and restore.

## Introduction

> WORKSAPCEs extend the **render space**. SCREENs extend the **display space**.

*VDM* embraces both *worksapce* and *screen-space*, which allows you to extract or archive your workloads along timeline.

You are free to re-define the usage of your workspaces and multi-screen, under facility of VDM.

While there are no system-side mechnism to manage the status of variety programs, VDM works as userspace program with plugins to fragment the functions of VDM (archive/extract). More plugins, More funs!

## Dependencies

Python 2.7.x (remains checked in installation script).

## Installation

* (optional) configure default `config.json`
* `mkdir build`
* `make check && make install`
* `domain-manager -h` for more help

## Usage

Todo list:

- ~~plugin API norm AND ctypes.cdll wrapper AND plugin proxy~~
- ~~domain manager (setup/restore/rename/delete)~~
- plugin manager (register/test/install/remove)
- plugin oracle with precompiled or website repository URI
- cross-platform compatability
- simple Tkinter GUI
- daemon for realtime plugin response

## Plugin Development

Please refer to the tutorial [here](plugin-template/README.md).

## License

Virtual Domain Manager is licensed under [GPLv3](LICENSE).
