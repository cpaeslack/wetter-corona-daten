#!/bin/bash
set -e

source .env
app="wetter-corona-daten"

docker build -t ${app}:${VERSION} .
docker run -d --rm \
  --name=${app} \
  -v $PWD:/app ${app}:${VERSION}