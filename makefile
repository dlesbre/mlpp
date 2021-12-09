PYTHON = python3
PIP = pip3
MYPY = mypy -p preproc
TEST = pytest
DIR = .

color = on

REQUIREMENTS = ./requirements-devel.txt

ifeq ($(color),on)
	# Bold orange text
	color_yellow = \033[33;1m
	color_orange = \033[33m
	color_reset  = \033[38;22m
else
	color_yellow=
	color_reset=
endif

# =============================
# Default target
# =============================

default: ## default target

# =============================
# Special Targets
# =============================

# No display of executed commands.
$(VERBOSE).SILENT:

.PHONY: default install install-devel mypy test

default: mypy test

install: ## install the package for use
	echo "$(color_yellow)Installing package$(color_reset)"
	$(PIP) install $(DIR)

install-devel: ## install and configure for development
	echo "$(color_yellow)Installing tools$(color_reset)"
	$(PIP) install -U $(PIP)
	$(PIP) install -r $(REQUIREMENTS)
	echo "$(color_yellow)Setting up pre-commit$(color_reset)"
	pre-commit uninstall
	pre-commit install
	echo "$(color_yellow)Installing package$(color_reset)"
	$(PIP) install -e $(DIR)

mypy: ## run mypy
	echo "$(color_yellow)Running mypy$(color_reset)"
	$(MYPY)

test: ## run the test suite (requires prior install)
	echo "$(color_yellow)Running pytest$(color_reset)"
	$(TEST)

help: ## Show this help
	@echo "$(color_yellow)make:$(color_reset) usefull targets:"
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(color_orange)%-14s$(color_reset) %s\n", $$1, $$2}'
