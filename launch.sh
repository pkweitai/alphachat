#!/bin/bash

PLIST_DIR=~/Library/LaunchAgents
BASE_NAME=com.storyflix.ainews

# Function to unload the plist
unload_plist() {
    local service=$1
    local plist_path="$PLIST_DIR/$BASE_NAME.$service.plist"
    if [ -f "$plist_path" ]; then
        launchctl bootout gui/$(id -u) "$plist_path"
        echo "Unloaded $service"
    else
        echo "Plist file for $service does not exist"
    fi
}

# Function to load the plist
load_plist() {
    local service=$1
    local plist_path="$PLIST_DIR/$BASE_NAME.$service.plist"
    if [ -f "$plist_path" ]; then
        launchctl bootstrap gui/$(id -u) "$plist_path"
        echo "Loaded $service"
    else
        echo "Plist file for $service does not exist"
    fi
}

# Check the arguments to determine which action to take
if [ "$1" == "app" ]; then
    if [ "$2" == "--unload" ]; then
        unload_plist app
    else
        load_plist app
    fi
elif [ "$1" == "searchnews" ]; then
    if [ "$2" == "--unload" ]; then
        unload_plist searchnews
    else
        load_plist searchnews
    fi
elif [ "$1" == "viq" ]; then
    if [ "$2" == "--unload" ]; then
        unload_plist viq
    else
        load_plist viq
    fi
else
    echo "Usage: $0 {app|searchnews} [--unload]"
    exit 1
fi

