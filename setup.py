#!/usr/bin/env python3
import re
from setuptools import find_packages, setup

_version = open('./VERSION').read()
_major = re.findall(r'VERSION_MAJOR\W+=\W+(\d+)', _version)[0]
_minor = re.findall(r'VERSION_MINOR\W+=\W+(\d+)', _version)[0]
try:
    _patch = re.findall(r'VERSION_PATCH\W+=\W+(\d+)', _version)[0]
except:
    _patch = '0'
_version = '.'.join((_major, _minor, _patch))

if __name__ == '__main__':
    setup(
        name = 'pyvdm',
        version = _version,
        description = 'Pyvdm is a simple python implementation for VDM.',
        url = 'https://github.com/VDM-Maintainer-Group/virtual-domain-manager',
        author = 'iamhyc',
        author_email = 'sudofree@163.com',
        #
        install_requires = ['PyQt5', 'posix-ipc'],
        package_dir = {'': 'build'},
        packages = find_packages(where='build'),
        package_data = {
            "pyvdm": ["assets/*"],
        },
        entry_points = {
            'console_scripts': [
                'pyvdm = pyvdm.core.manager:main',
                'pyvdm-tray = pyvdm.gui.tray:main'
            ]
        }
    )
