# See 'make help' for a list of useful targets

# ==================================================
# Constants
# ===================================================

PYTHON = python3
PIP = $(PYTHON) -m pip
MYPY = mypy -p mlpproc
PYTEST = pytest
DIR = .
PRECOMMIT = pre-commit

PACKAGE = mlpproc

# set to ON/OFF to toggle ANSI escape sequences
COLOR = ON

# Uncomment to show commands
# VERBOSE = TRUE

# padding for help on targets
# should be > than the longest target
HELP_PADDING = 15

# ==================================================
# Make code and variable setting
# ==================================================

ifeq ($(COLOR),ON)
	# Bold orange text
	color_yellow = \033[33;1m
	color_orange = \033[33m
	color_reset  = \033[38;22m
else
	color_yellow=
	color_orange=
	color_reset=
endif

define print
	@echo "$(color_yellow)$(1)$(color_reset)"
endef

# =============================
# Default target
# =============================

default: ## default target
.PHONY: default

# =============================
# Special Targets
# =============================

# No display of executed commands.
$(VERBOSE).SILENT:

.PHONY: help
help: ## Show this help
	@echo "$(color_yellow)make:$(color_reset) list of useful targets :"
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(color_blue)%-$(HELP_PADDING)s$(color_reset) %s\n", $$1, $$2}'

default: mypy test

.PHONY: precommit
precommit: ## run precommit
	$(call print,Running precommit)
	$(PRECOMMIT) run

.PHONY: precommit-all
precommit-all: ## run precommit on all files
	$(call print,Running precommit on all files)
	$(PRECOMMIT) run --all-files

.PHONY: test
test: ## Run all tests
	$(call print,Running pytest)
	$(PYTEST)

.PHONY: mypy
mypy: ## Typecheck all files
	$(call print,Running mypy)
	$(MYPY)

# =================================================
# Installation
# =================================================

.PHONY: setup
setup: ## Install dependencies
	$(call print,Upgrading pip)
	$(PIP) install --upgrade pip
	$(call print,Installing package and dependencies)
	$(PIP) install $(DIR)

.PHONY: setup-dev
setup-dev: ## Install development dependencies
	$(call print,Upgrading pip)
	$(PIP) install --upgrade pip
	$(call print,Installing package and development dependencies)
	$(PIP) install -e $(DIR)[dev]
	$(call print,Setting up pre-commit)
	$(PRECOMMIT) install

.PHONY: clean
clean: ## Remove package
	$(call print,Removing package)
	rm -rf build dist $(PACKAGE).egg-info .mypy_cache .pytest_cache

.PHONY: deploy
deploy: ## Build and deploys the package
	$(call print,Removing previous dist)
	rm -rf dist/*
	$(call print,Building package)
	$(PYTHON) setup.py bdist_wheel
	$(call print,Deploying package)
	twine upload dist/*
