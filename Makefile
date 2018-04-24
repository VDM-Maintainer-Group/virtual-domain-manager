
all:clean compile

check:
	@script/dependency.sh
compile:
	@script/compile.sh
install:cleandist compile
	@script/install.sh
uninstall:
	@script/uninstall.sh
clean:
	@script/clean.sh
cleandist:clean
	@rm -rf ./build