#!/usr/bin/env bash
set -e

docker build -t knutj42/vannpumpelogserver .
docker push knutj42/vannpumpelogserver
