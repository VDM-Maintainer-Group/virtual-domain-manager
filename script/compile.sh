#!/bin/bash
PWD=${0%/*}
printf "\t[Virtual Domain Manager Compiler]\n"
cd $PWD && cd ..
sudo echo

printf "\t======== Compile & Build ========\n"
# make in bin/
printf "[Compiling]\tBinary Source\n"
cd bin && make && cd ..
printf "\r[COMPILED] \tBinary Source\n"
# run python compile
printf "[Compiling]\tPython Source "
python -m compileall -fq helper manager plugins
python -m compileall -fq domain-manager.py
mv domain-manager.pyc domain-manager && sudo chmod 755 domain-manager
printf "\r[COMPILED] \tPython Source\n"
# copy to build
rm -rf $PWD/build && mkdir $PWD/build
rsync -rq --exclude-from $PWD'/exclude.rsync' $PWD/* $PWD/build

printf "\t========     Complete!    ========\n\n"
