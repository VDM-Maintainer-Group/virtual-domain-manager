#!/bin/bash

# dependency check
function pkg_check(){
	pkg=$1;
	printf "[PENDING]\t%s " $pkg
	sudo apt-get install -y $pkg 1> /dev/null
	printf "\r[INSTALLED]\t%s\n" $pkg
}

function grep_json_item(){
	data=`(cat "config.json")|grep $1|awk -F ":" '{print $2}'`
	data=${data%\",*}
	echo ${data#\"*}
}

printf "\t======== Dependency Check ========\n"
sudo echo
pkg_check "python-wnck"
pkg_check "rsync"
echo

printf "\t========   Installation   ========\n"
# python setup.py install
item=`grep_json_item "install-dir"`
# install to config.install_dir
# sudo cp -r ./ $item
# add install_dir to path
if [[ ! $PATH =~ $item ]]; then
	echo "export PATH=\$PATH:$item" >> ~/.bashrc
	source ~/.bashrc
fi
echo

printf "\t========     Complete!    ========\n"
