#!/usr/bin/env python3
import re, os
from setuptools import find_packages, setup

_version = open('./VERSION').read()
_major = re.findall(r'VERSION_MAJOR\W+=\W+(\d+)', _version)[0]
_minor = re.findall(r'VERSION_MINOR\W+=\W+(\d+)', _version)[0]
try:
    _patch = re.findall(r'VERSION_PATCH\W+=\W+(\d+)', _version)[0]
except:
    _patch = '0'
_version = '.'.join((_major, _minor, _patch))

from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
class bdist_wheel(_bdist_wheel):
    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        self.root_is_pure = False
        pass

    def get_tag(self):
        (impl, abi, plat_name) = _bdist_wheel.get_tag(self)
        impl, abi = 'py3', 'none'
        return (impl, abi, plat_name)
    pass

if __name__ == '__main__':
    setup(
        name = 'pyvdm',
        version = _version,
        description = 'Pyvdm is a simple python implementation for VDM.',
        url = 'https://github.com/VDM-Maintainer-Group/virtual-domain-manager',
        author = 'iamhyc',
        author_email = 'sudofree@163.com',
        #
        install_requires = ['PyQt5', 'posix-ipc', 'psutil', 'requests',
                            'dbus-python', 'halo', 'termcolor', 'pyyaml'],
        package_dir = {'': 'build'},
        packages = find_packages(where='build'),
        package_data = {
            "" : ["daemon/*.so"],
            "pyvdm": ["assets/*", "assets/*/*"],
        },
        include_package_data=True,
        entry_points = {
            'console_scripts': [
                'pyvdm = pyvdm.core.manager:main',
                'pyvdm-tray = pyvdm.gui.tray:main',
                'sbs = pyvdm.build:main'
            ]
        },
        cmdclass={
            'bdist_wheel': bdist_wheel,
        }
    )
