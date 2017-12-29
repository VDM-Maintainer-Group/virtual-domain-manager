#!/bin/bash
PWD=${0%/*}
cd $PWD && cd ..

rm -f domain-manager
rm -rf build
find . -name "*.pyc" -exec rm -f {} \;
echo "Cleaned."
