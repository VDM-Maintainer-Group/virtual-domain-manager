#!/bin/bash
sudo echo
# dependency check
function pkg_check(){
	pkg=$1;
	printf "[PENDING]\t%s " $pkg
	sudo apt-get install -y $pkg 1> /dev/null
	if [[ $? -ne 0 ]]; then
		printf "[apt-get]\t%s fail.\n" $pkg
	 	exit -1
	fi
	printf "\r[INSTALLED]\t%s\n" $pkg
}

function pip_check(){
	pkg=$1;
	printf "[PENDING]\tpython-%s " $pkg

	pkg_status=`pip freeze 2>/dev/null|grep $pkg`
	if [[ -z $pkg_status ]]; then
		sudo pip install $pkg 1> /dev/null
		if [[ $? -ne 0 ]]; then
			printf "[pip]\t%s fail.\n" $pkg
			exit -1
		fi
	fi

	printf "\r[INSTALLED]\tpython-%s\n" $pkg
}

printf "\t======== Dependency Check ========\n"
pkg_check "rsync"
pkg_check "python-pip"
pkg_check "python-wnck" 
pkg_check "python-dbus"
pip_check 'termcolor'
pip_check 'crcmod'
pip_check 'greenlet'

printf "\t========     Complete!    ========\n\n"
