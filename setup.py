#! /usr/bin/python
"""
Domain Manager
-----


"""
from setuptools import setup, find_packages

setup(
    name='domain-manager',
    version='0.10',
    url='https://github.com/iamhyc/domain-manager.git',
    license='LGPL',
    keywords='domain-manager',
    author='Mark Hong',
    author_email='sudofree@163.com',
    description='Domain manager for super workspace',
    long_description = 'Domain manager for super workspace',  
    packages=find_packages(),
    platforms='any',
    include_package_data = True,
    install_requires=[
        'dbus', 'wnck', 'termcolor', 
        'crcmod'
    ],
    extras_require={
        'dotenv': ['python-dotenv'],
        'dev':[
            'greenlet'
        ],
    },
    entry_points:{
        'console-scripts':[
            'test = Scripts.test:main',
        ]
    },
    zip_false=False
)
