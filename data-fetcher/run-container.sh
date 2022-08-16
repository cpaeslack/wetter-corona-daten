#!/bin/bash
set -e

source .env
app="data-fetcher"

docker build -t ${app}:${VERSION} .
docker run -d --rm \
  --name=${app} \
  -v $PWD:/app ${app}:${VERSION}
