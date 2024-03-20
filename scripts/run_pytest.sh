#!/bin/bash

# Navigate to the root directory of your project
cd "$(dirname "$0")"/..

# Set PYTHONPATH for this session only
export PYTHONPATH=$(pwd):$PYTHONPATH

# Run pytest
pytest "$@"

