#!/bin/bash

# Ensure the correct environment is activated
source /Users/rexching/miniconda3/bin/activate ainews
source ~/envlist

# Check the first argument to determine which script to run
if [ "$1" == "app" ]; then
    cd ~/ainews/
    python app.py --prod
elif [ "$1" == "searchnews" ]; then
    cd ~/ainews/
    python searchnews.py
elif [ "$1" == "viq" ]; then
    cd ~/ainews/
   python audioService.py --server
else
    echo "Usage: $0 {app|searchnews}"
    exit 1
fi

