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

	pkg_status=`pip3 freeze 2>/dev/null|grep $pkg`
	if [[ -z $pkg_status ]]; then
		sudo pip3 install $pkg 1> /dev/null
		if [[ $? -ne 0 ]]; then
			printf "[pip3]\t%s fail.\n" $pkg
			exit -1
		fi
	fi

	printf "\r[INSTALLED]\tpython-%s\n" $pkg
}

printf "\t======== Dependency Check ========\n"
pkg_check "rsync"
pkg_check "python3"
pkg_check "python3-pip"
pkg_check "python3-gi" 
pkg_check "gir1.2-wnck-3.0"
pkg_check "python3-dbus"
pip_check 'termcolor'
pip_check 'crcmod'
pip_check 'greenlet'

printf "\t========     Complete!    ========\n\n"
