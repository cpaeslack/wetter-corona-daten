#!/bin/bash
set -e

source .env
app="db-age-notifier"

docker build -t ${app}:${VERSION} .
docker run -d --rm \
  --name=${app} \
  -v $PWD:/app ${app}:${VERSION}