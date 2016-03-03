[![codecov.io](https://codecov.io/github/mozilla-services/push-messages/coverage.svg?branch=master)](https://codecov.io/github/mozilla-services/push-messages?branch=master) [![Build Status](https://travis-ci.org/mozilla-services/push-messages.svg?branch=master)](https://travis-ci.org/mozilla-services/push-messages)

# Push Messages API

A [swagger](http://swagger.io/) driven Pyramid app that utilizes Redis for
recent messages sent into the Mozilla Push System and manages crypto public keys
that should have their recent message history recorded.

## Architecture

This project provides an internal API for the Mozilla Push Developer Dashboard.
Developers are identified by their registered VAPID public keys. A separate
process populates those keys to a Redis database.

### DynamoDB Table

Stores a permanent list of VAPID public keys that should have their message
metadata extracted from the Mozilla Push Service logstream.

This is a very lightly used table managed by `push_messages`.

### Redis

Stores a circular list of recent message metadata, indexed by VAPID public key.
`push_messages` can retrieve this data via API calls. Redis supports efficient
access/retrieval and has trim operations to emulate a circular list structure
efficiently.

## Developing

Checkout this repo, you will need Redis installed and a local DynamoDB to test
against.

Then:

    $ virtualenv pmenv
    $ source pmenv/bin/activate
    $ pip install -r requirements.txt
    $ python setup.py develop

Edit the `development.ini` to point to your Redis database and set the DynamoDB
table name to use.

Run the app locally:

    $ pserve development.ini

It will then let you know where you can reach it.
