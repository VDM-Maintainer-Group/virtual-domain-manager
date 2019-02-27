# Vritual Domain Manager

Virtual Domain Manager (VDM) is for fast virtual workspace content *setup, archieve and restore*.

## Introduction

VDM embraces both concept *worksapce* and *screen-space*, which allows you to archive and reload your workloads, at any place, at any time.

While there are no system-side mechnism to manage the status of variety programs (Windows 10 is trying hard on its [Timeline](https://support.microsoft.com/en-us/help/4230676/windows-10-get-help-with-timeline)), VDM works dedicatedly on GNU/Linux platforms with plugins integrated to implement the archive&extract functions.

More plugins, More funs!

## Dependencies

Python 3.7+

## Installation

1. (optional) configure default `config.json`
2. `mkdir build`
3. `make check && make install`
4. `domain-manager -h` for more help

## Usage

Todo list:

- domain manager (setup/restore/rename/delete)
- plugin manager (register/test/install/remove)
- plugin oracle (fetch plugin from website repository URI)
- PyQt GUI
- backend daemon

## Plugin Development

Please refer to the tutorial [here](plugins/template/README.md).

## License

Virtual Domain Manager is licensed under [GPLv3](LICENSE).
