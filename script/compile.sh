#!/bin/bash
PWD=${0%/*}
printf "\t[Virtual Domain Manager Compiler]\n"
cd $PWD && cd ..
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
	sudo pip install $pkg 1> /dev/null
	if [[ $? -ne 0 ]]; then
		printf "[pip]\t%s fail.\n" $pkg
	 	exit -1
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

echo
printf "\t======== Compile & Build ========\n"
# make in bin/
printf "[Compiling]\tBinary Source\n"
cd bin && make && cd ..
printf "\r[COMPILED] \tBinary Source\n"
# run python compile
printf "[Compiling]\tPython Source "
python -m compileall -qf utility wrapper manager plugins domain-manager.py
mv domain-manager.pyc domain-manager && sudo chmod 755 domain-manager
printf "\r[COMPILED] \tPython Source\n"
# copy to build
rm -rf $PWD/build && mkdir $PWD/build
rsync -rq --exclude-from $PWD'/exclude.rsync' $PWD/* $PWD/build

printf "\t========     Complete!    ========\n\n"
