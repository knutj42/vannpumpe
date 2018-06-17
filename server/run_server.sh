#!/usr/bin/env bash

set -e

python3.6 -m venv .python_venv

. ./.python_venv/bin/activate

pip install --no-cache-dir -r ./vannpumpelogserver/requirements.txt
pip install -e ./vannpumpelogserver

python run_server.py
