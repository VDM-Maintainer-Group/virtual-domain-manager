#!/bin/bash
PWD=${0%/*}
printf "\t[Virtual Domain Manager Installer]\n"
cd $PWD && cd ..
sudo echo

function grep_json_item(){
	data=`(cat $PWD/config.json)|grep $1|awk -F ":" '{print $2}'`
	data=${data%\",*}
	echo ${data#\"*}
}

printf "\t========   Installation   ========\n"
read -p "Press Enter to continue..."
# python setup.py install
item=`grep_json_item "install-dir"`
# install to config.install_dir
sudo mkdir -p $item && sudo cp -rf $PWD/build/* $item
printf "[Install]\tInstalled in: %s\n" $item
# create soft link to path
sudo ln -sf $item/domain-manager /usr/bin/
printf "[Install]\tEntrance soft link created\n"

printf "\t========     Complete!    ========\n\n"
