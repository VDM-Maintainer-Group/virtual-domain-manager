`# Vritual Domain Manager

Virtual Domain Manager is for fast virtual workspace setup, archieve and restore.

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
- plugin manager (register/test/install/remove)
- ~~domain manager (setup/restore/rename/delete)~~
- plugin oracle with precompiled or website repository URI
- cross-platform compatability
- simple Tkinter GUI
- daemon for realtime plugin response

## Plugin Development

Please refer to the tutorial [here](plugin-template/README.md).

## License

Virtual Domain Manager is licensed under [GPLv3](LICENSE).
