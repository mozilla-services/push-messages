SHELL := /bin/sh
APPNAME = push_messages
HERE = $(shell pwd)

.PHONY: all travis $(HERE)/ddb

all:	travis

travis: $(HERE)/ddb
	pip install tox

$(HERE)/ddb:
	mkdir $@
	curl -sSL http://dynamodb-local.s3-website-us-west-2.amazonaws.com/dynamodb_local_latest.tar.gz | tar xzvC $@
