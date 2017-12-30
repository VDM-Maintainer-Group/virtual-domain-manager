#!/bin/bash
PWD=${0%/*}
printf "\t[Virtual Domain Manager Uninstaller]\n"
cd $PWD && cd ..
sudo echo

function grep_json_item(){
	data=`(cat $PWD/config.json)|grep $1|awk -F ":" '{print $2}'`
	data=${data%\",*}
	echo ${data#\"*}
}

printf "\t========  Uninstallation  ========\n"
read -p "Press Enter to continue..."
item=`grep_json_item "install-dir"`
sudo rm -rf $item
sudo rm -f /usr/bin/domain-manager

echo "Uninstalled."