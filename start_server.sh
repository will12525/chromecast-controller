#!/bin/bash
set -x
trap 'kill 0' SIGTERM
source source .venv/bin/activate
python run.py $1
CMD_EXIT_CODE=$?

exit $CMD_EXIT_CODE
