#!/usr/bin/env python3
from setuptools import find_packages, setup
from core.pyvdm.utils import WorkSpace

if __name__ == '__main__':
    with WorkSpace('./build') as ws:
        print( find_packages() )
        setup(
            name = 'pyvdm',
            version = '0.1.0',
            description = 'Pyvdm is a simple python implementation for VDM.',
            url = 'https://github.com/VDM-Maintainer-Group/virtual-domain-manager',
            author = 'iamhyc',
            author_email = 'sudofree@163.com',
            #
            install_requires = ['PyQt5'],
            packages = find_packages(),
            entry_points = {
                'console_scripts': [
                    'pyvdm = package.core.manager:main',
                    'pyvdm-tray = package.gui.tray:main'
                ]
            }
        )
        pass