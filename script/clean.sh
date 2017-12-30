#!/bin/bash
PWD=${0%/*}
cd $PWD && cd ..

rm -f domain-manager
find . -name "*.pyc" -exec rm -f {} \;
echo "Cleaned."
