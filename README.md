# Virtual Domain Manager



https://user-images.githubusercontent.com/9068301/203792081-b69e406d-8283-4e0f-bc97-fa009d8b2674.mp4



## Introduction

[Project Progress](https://github.com/VDM-Maintainer-Group/virtual-domain-manager/issues/3)

<p align="center">
  <img src="./previews/structure.png" width="650px" />
</p>

- VDM is "container": it starts GUI applications in isolated namespace;

- VDM is "snapshot": it keeps the status of last exit when starts up;

- VDM is "tree-like": it can traverse each divergence, like time machine;

- VDM is NOT "virtual machine": it cares only GUI applications status, not memory.

## Dependencies

- System-related dependencies
  ```bash
  # for Debian-based distributions
  sudo apt install build-essential curl cmake git python3-pip libdbus-1-dev libglib2.0-dev
  ```

- [Rust toolchain](https://www.rust-lang.org/tools/install)
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  ```

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

## Usage

Currently, the VDM command-line entry is `pyvdm`, and the GUI entry is `pyvdm-tray`.

The overview of command-line usage is listed below.

- **Domain Switch** `pyvdm [--open] [--save] [--close]`

- **Domain Management** `pyvdm domain`

- **Plugin Management** `pyvdm plugin`

- **Capability Management** `pyvdm capability`

- **Compatibility Report** `pyvdm application`

- **Sync Management** `pyvdm sync`
  > (Not implemented) Manage synchronization of domain status files and data files.

## Compatibility

### Native
- Firefox ESR (via [browser-bridge](https://github.com/VDM-Maintainer-Group/vdm-capability-library/tree/main/browser-bridge))
- Google Chrome (via [browser-bridge](https://github.com/VDM-Maintainer-Group/vdm-capability-library/tree/main/browser-bridge))
- Microsoft Edge (via [browser-bridge](https://github.com/VDM-Maintainer-Group/vdm-capability-library/tree/main/browser-bridge))
- Deepin Browser (via [browser-bridge](https://github.com/VDM-Maintainer-Group/vdm-capability-library/tree/main/browser-bridge))

### Plugins
|                            Plugin                            |          Target           |
| :----------------------------------------------------------: | :-----------------------: |
| [vdm-vscode-plugin](https://github.com/VDM-Maintainer-Group/vdm-vscode-plugin/releases/latest) |      "code.desktop"       |
| [vdm-vlc-plugin](https://github.com/VDM-Maintainer-Group/vdm-vlc-plugin/releases/latest) |       "vlc.desktop"       |
| [vdm-typora-plugin](https://github.com/VDM-Maintainer-Group/vdm-typora-plugin/releases/latest) |    "io.typora.desktop"    |
| [vdm-okular-plugin](https://github.com/VDM-Maintainer-Group/vdm-okular-plugin/releases/latest) | "org.kde.okular.desktop"  |
| [desktop-settings-plugin](https://github.com/VDM-Maintainer-Group/desktop-settings-plugin/releases/latest) | Wallpaper, Network, Audio |


## Capability Development

> The `VDM Capability Library` is developed to be invoked by `VDM Plugin` for alleviation of complicated development.
> The library should provide a entry with functions exported with specific type of signature.

Please refer to the contribution guidance [here](https://github.com/VDM-Maintainer-Group/vdm-capability-library/blob/main/CONTRIBUTING.md).

## Plugin Development

> The `VDM Plugin` implements `SRC interface` and is invoked by `VDM Core`.
> The plugin is developed to support GUI application compatibility, or define the actions to be taken when switch the domain.

Please refer to the development guidance [here](https://github.com/VDM-Maintainer-Group/vdm-plugin-template/blob/master/CONTRIBUTING.md).


## License

Virtual Domain Manager is licensed under [GPLv3](LICENSE).
