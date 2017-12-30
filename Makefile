
all:clean compile

compile:
	@script/compile.sh
install:compile
	@script/install.sh
uninstall:
	@script/uninstall.sh
clean:
	@script/clean.sh