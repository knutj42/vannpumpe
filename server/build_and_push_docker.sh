#!/usr/bin/env bash
set -e

docker build -t knutj42/vannpumpelogserver .
docker push knutj42/vannpumpelogserver

ssh knutj@robots.knutj.org "docker pull knutj42/vannpumpelogserver && docker-compose up -d && docker logs -f knutj_vannpumpelogserver_1"

