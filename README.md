# Virtual Domain Manager



https://user-images.githubusercontent.com/9068301/203792081-b69e406d-8283-4e0f-bc97-fa009d8b2674.mp4

[Project Progress](https://github.com/VDM-Maintainer-Group/virtual-domain-manager/issues/3)

## Introduction

**VDM is a workspace manager for GUI applications.**

When workspace is closing, VDM will save the status of all [*compatible applications*](#compatibility) and restore them when re-open.


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

5. **run pyvdm**

    ```bash
    pyvdm-tray
    ```
    > or `pyvdm` for command-line interface.


## Compatibility

Currently, VDM detects the compatibility of applications in the following two ways:

### Native Compatibility
> The compatibility is claimed over [D-Bus](./interface/org.vdm-compatible.src.xml).

- Firefox ESR    (via [browser-bridge](./capability/browser-bridge))
- Google Chrome  (via [browser-bridge](./capability/browser-bridge))
- Microsoft Edge (via [browser-bridge](./capability/browser-bridge))
- Deepin Browser (via [browser-bridge](./capability/browser-bridge))

### Plugin-based Compatibility
> The compatibility is claimed by installed plugins.

|                            Plugin                            |          Target           |
| :----------------------------------------------------------: | :-----------------------: |
| [vdm-vscode-plugin](https://github.com/VDM-Maintainer-Group/vdm-vscode-plugin/releases/latest) |      "code.desktop"       |
| [vdm-vlc-plugin](https://github.com/VDM-Maintainer-Group/vdm-vlc-plugin/releases/latest) |       "vlc.desktop"       |
| [vdm-typora-plugin](https://github.com/VDM-Maintainer-Group/vdm-typora-plugin/releases/latest) |    "io.typora.desktop"    |
| [vdm-okular-plugin](https://github.com/VDM-Maintainer-Group/vdm-okular-plugin/releases/latest) | "org.kde.okular.desktop"  |
| [desktop-settings-plugin](https://github.com/VDM-Maintainer-Group/desktop-settings-plugin/releases/latest) | Wallpaper, Network, Audio |

## Development

The architecture of VDM is split into three parts: `VDM Core` `VDM Capability Library`, and `VDM Plugin`.

<p align="center">
  <img src="./previews/structure.png" width="650px" />
</p>

### Capability Development

> The `VDM Capability Library` is developed to be invoked by `VDM Plugin` for alleviation of complicated development.
> The library should provide a entry with functions exported with specific type of signature.

Please refer to the contribution guidance [here](https://github.com/VDM-Maintainer-Group/vdm-capability-library/blob/main/CONTRIBUTING.md).

### Plugin Development

> The `VDM Plugin` implements `SRC interface` and is invoked by `VDM Core`.
> The plugin is developed to support GUI application compatibility, or define the actions to be taken when switch the domain.

Please refer to the contribution guidance [here](https://github.com/VDM-Maintainer-Group/vdm-plugin-template/blob/master/CONTRIBUTING.md).


## License

Virtual Domain Manager is licensed under [GPLv3](LICENSE).
