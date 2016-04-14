#!/bin/sh

exec gunicorn push_messages.wsgi:application -b 0.0.0.0:${PORT:-8000} --log-file -
