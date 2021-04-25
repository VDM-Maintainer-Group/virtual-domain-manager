# Virtual Domain Manager

<!-- Virtual Domain Manager (VDM) is a *Plan B* to take snapshot of the running status of operating system, by *archive, restore and synchronize* your applications, for fast arranging your workloads. -->

> *NEED A DEMO GIF HERE.*

## Introduction

<!-- How to take a snapshot of a running operating system, and somehow restore from it?

- **Plan A**: request status of *hardwares* (CPU, Memory, Storage) and record them all.
- **Plan B**: request status of *softwares* (users' applications) and record them all.

As "Plan A" is straightforward (e.g., virtual machine) but always with high overhead, we believe "Plan B" (e.g., [CRIU](https://github.com/checkpoint-restore/criu)) is the future.

This project, VDM, is a non-serious-but-effective "Plan B" design. Focusing on the running status of all your GUI applications on **multiple-desktop / multiple-screen / multiple-device**, VDM would like to arrange them according to your **working domain** definition.

In the open working domain, VDM would request all the support applications to report their necessary running status (open files, window status and etc.), record them for future restore. Unfortunately, while there are no such status-report APIs, VDM proposes a **plugin mechanism** to implement such support and provides **capability library** to simplify the development.

<p align="center">
  <img src="./previews/structure.png" width="650px" />
</p>

> VDM is now dedicated developed on GNU/Linux platform and highly coupled with Linux kernel.
>
> Currently, we are seeking for help on: plugin development, capability library contribution, and any suggestions. If you want to join the maintainer team, please [contact us](mailto:sudofree_at_163_com). -->

## Installation

1. **clone this repository**

   ```bash
   git clone https://github.com/VDM-Maintainer-Group/virtual-domain-manager.git --depth=1
   git submodule update --init
   ```

2. **build with cmake** (>=3.10)

   ```bash
   mkdir build; cd build; cmake ..; make
   cd build; make build-pyvdm
   ```

3. **install the capability library and pyvdm**

   ```bash
   cd build; sudo make install
   cd dist; pip3 install *.whl
   ```

## Usage

> Currently, the VDM main program is `pyvdm`, the GUI entry is a tray icon `pyvdm-tray`.

- **Workload Manipulation**

  `pyvdm --open <domain-name>` to open an existing domain;

  `pyvdm --save` to save current domain;

  `pyvdm --close` to close current domain;

  Or, you can easily apply above operations via `pyvdm-tray` on your dock.

- **Plugin Management**

  - install a plugin: `pyvdm plugin install <path-to-plugin-archive-file>`
  - uninstall plugin(s): `pyvdm plugin uninstall <plugin1> [<plugin2> ...]`
  - list plugin(s) details: `pyvdm plugin list [<plugin-name>]`
  - run plugin functions: `pyvdm plugin run <plugin-name> <function-name>`

- **Domain Management**

  - add a domain via TUI: `pyvdm domain add <domain-name>`
  - update a domain via TUI: `pyvdm domain update <domain-name>`
  - remove a domain: `pyvdm domain remove <domain-name>`
  - list domain(s) details: `pyvdm domain list [<domain-name>]`

- **Capability Management**

  > Manage capability installation, enabling and running status.

  (To be updated ...)

- **Sync Management**

  > Manage synchronization of domain status files.

  (To be updated ...)

## Capability Development

Please refer to the tutorial [here](https://github.com/VDM-Maintainer-Group/vdm-capability-library/).

## Plugin Development

Please refer to the tutorial [here](https://github.com/VDM-Maintainer-Group/vdm-plugin-template/CONTRIBUTING.md).

## License

Virtual Domain Manager is licensed under [GPLv3](LICENSE).
