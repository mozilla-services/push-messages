SHELL := /bin/sh
APPNAME = push_messages
HERE = $(shell pwd)

.PHONY: all travis $(HERE)/ddb

all:	travis

travis:
	pip install tox
