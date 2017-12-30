
all:clean check compile

check:
	@script/dependency.sh
compile:
	@script/compile.sh
install:compile
	@script/install.sh
uninstall:
	@script/uninstall.sh
clean:
	@script/clean.sh
cleandist:clean
	@rm -r ./build