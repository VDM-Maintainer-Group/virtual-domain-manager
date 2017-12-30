# Vritual Domain Manager

Virtual Domain Manager is for fast virtual workspace setup, archieve and restore.

## Dependencies

Python 3.x (remains checked in installation script).

## Installation

* (optional) configure default `config.json`
* `mkdir build`
* `make check && make install`
* `domain-manager -h` for more help

## Usage

Todo list:

- plugin API norm AND ctypes.cdll wrapper AND plugin proxy
- plugin manager (register/test/install/remove)
- manager daemon; setup/restore/rename/delete
- simple Tkinter GUI
- cross-platform degradation

## Plugin Development

Please refer to the tutorial [here](plugin-template/README.md).

## License

Virtual Domain Manager is licensed under [GPLv3](LICENSE).