#!/usr/bin/env python3
from setuptools import find_packages, setup
from core.pyvdm.utils import WorkSpace

if __name__ == '__main__':
    setup(
        name = 'pyvdm',
        version = '0.1.0',
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
