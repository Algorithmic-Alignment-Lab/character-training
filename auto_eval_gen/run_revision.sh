#!/bin/bash
export PYTHONPATH=$(pwd)/..:$PYTHONPATH
python scripts/revision.py "$@"
