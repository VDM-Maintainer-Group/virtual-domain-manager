#!/bin/bash
PWD=${0%/*}
printf "\t[Virtual Domain Manager Compiler]\n"
cd $PWD && cd ..
sudo echo

printf "\t======== Compile & Build ========\n"
# make in bin/
printf "[Compiling]\tBinary Source"
cd bin && make 1> /dev/null && cd ..
printf "\r[COMPILED] \tBinary Source\n"

# run python compile
printf "[Compiling]\tPython Source "
python -m compileall -fq helper plugins
python -m compileall -fq manager.py
mv manager.pyc domain-manager && sudo chmod 755 domain-manager
printf "\r[COMPILED] \tPython Source\n"

# copy to build
rm -rf $PWD/build && mkdir $PWD/build
rsync -rq --exclude-from $PWD'/scripts/exclude.rsync' $PWD/* $PWD/build

printf "\t========     Complete!    ========\n\n"
