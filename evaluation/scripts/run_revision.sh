#!/bin/bash
export PYTHONPATH=$(dirname $(pwd))/..:$PYTHONPATH
python $(dirname "$0")/revision.py "$@"
