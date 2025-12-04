# Makefile for Python project

.DELETE_ON_ERROR:
.PHONY: FORCE
.PRECIOUS:
.SUFFIXES:

SHELL:=/bin/bash -e -o pipefail
SELF:=$(firstword $(MAKEFILE_LIST))

PKG=anyvlm
PKGD=$(subst .,/,${PKG})
PYV:=3.11
VEDIR=venv/${PYV}

UNAME = $(shell uname)
ifeq (${UNAME},Darwin)
    _XRM_R:=
else
    _XRM_R:=r
endif
XRM=xargs -0${_XRM_R} rm

############################################################################
#= BASIC USAGE
default: help

#=> help -- display this help message
help:
	@sbin/makefile-extract-documentation "${SELF}"


############################################################################
#= SETUP, INSTALLATION, PACKAGING

#=> venv: make a Python 3 virtual environment & install basic dependencies
.PHONY: venv/%
venv/%:
	python$* -m venv $@; \
	. $@/bin/activate; \
	python -m ensurepip --upgrade; \
	pip install --upgrade pip setuptools; \
	pip install .

#=> develop: install package in develop mode
.PHONY: develop
develop:
	pip install -e .[test]

#=> devready: create venv, install prerequisites, install pkg in develop mode
.PHONY: devready
devready:
	make ${VEDIR} && source ${VEDIR}/bin/activate && make develop
	@echo '################################################################'
	@echo '###  `source ${VEDIR}/bin/activate` to use this environment  ###'
	@echo '################################################################'

#=> install: install package
#=> bdist bdist_egg bdist_wheel build sdist: distribution options
.PHONY: bdist bdist_egg bdist_wheel build build_sphinx sdist install
bdist bdist_egg bdist_wheel build sdist install: %:
	python setup.py $@

############################################################################
#= TESTING
# see test configuration in setup.cfg

.PHONY: testready
testready:
	pip install -e '.[postgres,queueing,test]'

#=> test: execute tests
.PHONY: test
test:
	python -m pytest tests

#=> cqa: execute code quality tests
cqa:
	ruff format --check
	ruff check

#=> reformat: reformat code
.PHONY: reformat
reformat:
	ruff check --fix
	ruff format

############################################################################
#= CLEANUP

#=> clean: remove temporary and backup files
.PHONY: clean
clean:
	find . \( -name \*~ -o -name \*.bak \) -print0 | ${XRM}

#=> cleaner: remove files and directories that are easily rebuilt
.PHONY: cleaner
cleaner: clean
	rm -rf .cache *.egg-info .pytest_cache build dist doc/_build htmlcov
	find . \( -name \*.pyc -o -name \*.orig -o -name \*.rej \) -print0 | ${XRM} -fr
	find . -name __pycache__ -print0 | ${XRM} -fr
	rm -fvr .ruff_cache

#=> cleanest: remove files and directories that require more time/network fetches to rebuild
.PHONY: cleanest
cleanest: cleaner
	rm -fr .eggs .venv
