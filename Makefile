
all:clean compile

check:
	@scripts/dependency.sh
compile:
	@scripts/compile.sh
install:cleandist compile
	@scripts/install.sh
uninstall:
	@scripts/uninstall.sh
clean:
	@scripts/clean.sh
cleandist:clean
	@rm -rf ./build