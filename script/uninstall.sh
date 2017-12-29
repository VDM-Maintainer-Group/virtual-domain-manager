#!/bin/bash
printf "\t      [Virtual Domain Manager]      \n"
sudo echo

function grep_json_item(){
	data=`(cat $PWD/config.json)|grep $1|awk -F ":" '{print $2}'`
	data=${data%\",*}
	echo ${data#\"*}
}

read -p "Press Enter to continue..."
item=`grep_json_item "install-dir"`
sudo rm -rf $item
sudo rm -f /usr/bin/domain-manager

echo "Uninstalled."