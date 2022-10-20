# Virtual Domain Manager

[中文简介 - deepin论坛](https://bbs.deepin.org/zh/post/219493)


## Introduction
<p align="center">
  <img src="./previews/structure.png" width="650px" />
</p> 

## Dependencies

- System-related dependencies
  ```bash
  # for Debian-based distributions
  sudo apt install build-essential curl cmake git python3-pip libdbus-1-dev libglib2.0-dev
  ```

- [Rust toolchain](https://www.rust-lang.org/tools/install)

## Installation

1. **clone this repository**

   ```bash
   git clone https://github.com/VDM-Maintainer-Group/virtual-domain-manager.git --depth=1
   git submodule update --init
   ```

2. **build with cmake** (>=3.10)

   ```bash
   mkdir build; cd build; cmake ..; make
   ```

3. **build and install pyvdm**

   ```bash
   cd build; make build-pyvdm
   cd dist; pip3 install *.whl
   ```

4. **build and install capability library**

    ```bash
    cd capability; sbs build; sbs install
    ```

## Usage for Command Line

> Currently, the VDM main program is `pyvdm`, the GUI entry is a tray icon `pyvdm-tray`.

- **Workload Manipulation**

  `pyvdm --open <domain-name>` to open an existing domain;

  `pyvdm --save` to save current domain;

  `pyvdm --close` to close current domain;

  Or, you can easily apply above operations via `pyvdm-tray` on your dock.

- **Plugin Management** `pyvdm plugin`

  - `install` a plugin with the "*.zip" file
  - `uninstall` existing plugin(s) with `name(s)`
  - `list` plugin details (list all by default)
  - `run` plugin functions with:

    `pyvdm plugin run <plugin-name> <function-name>`

- **Domain Management** `pyvdm domain`

  - `add` a domain via TUI with `name`
  - `update` an existing domain with `name`
  - `remove` an existing domain with `name`
  - `list` domain details (list all by default)

- **Capability Management** `pyvdm capability`

  - `install` capability from folder or "*.zip" file
  - `uninstall` capability with `name`
  - `enable`/`disable`/`query` capability status
  - capability daemon status:

    `pyvdm capability daemon start/stop/restart/status`

- **Sync Management** `pyvdm sync`

  > Manage synchronization of domain status files.

  (To be updated ...)

## Capability Development

Please refer to the guidance [here](https://github.com/VDM-Maintainer-Group/vdm-capability-library/blob/main/CONTRIBUTING.md).

## Plugin Development

Please refer to the guidance [here](https://github.com/VDM-Maintainer-Group/vdm-plugin-template/blob/master/CONTRIBUTING.md).


## License

Virtual Domain Manager is licensed under [GPLv3](LICENSE).
