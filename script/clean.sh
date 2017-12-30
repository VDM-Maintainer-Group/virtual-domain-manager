#!/bin/bash
PWD=${0%/*}
cd $PWD && cd ..

rm -f domain-manager
find . -name "*.pyc" -exec rm -f {} \;
find . -name "__pycache__" -exec rm -rf {} \;
echo "Cleaned."
