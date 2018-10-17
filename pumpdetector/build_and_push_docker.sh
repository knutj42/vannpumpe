#!/usr/bin/env bash
set -e

docker build -t knutj42/pumpdetector .
docker push knutj42/pumpdetector

ssh knutj@robots.knutj.org "docker pull knutj42/pumpdetector && docker-compose up -d && docker logs -f knutj_pumpdetector_1"

