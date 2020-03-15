#!/bin/bash

set -e  # exit immediately on any errors with non zero exit status

dockerize -wait tcp://$PG_HOST:$PG_PORT -timeout 60s -- python manage.py migrate --noinput

exec "$@"
