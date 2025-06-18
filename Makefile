# Makefile to clone @meamy/t-par and run its Makefile

REPO_URL = https://github.com/meamy/t-par.git
REPO_DIR = t-par

.PHONY: all clone run-make clean

all: clone run-make

clone:
	@if [ ! -d "$(REPO_DIR)" ]; then \
		git clone $(REPO_URL) $(REPO_DIR); \
	else \
		echo "$(REPO_DIR) already exists, skipping clone."; \
	fi

run-make: clone
	@cd $(REPO_DIR) && $(MAKE)

clean:
	@rm -rf $(REPO_DIR)