#!/bin/bash

# Check if an image name is provided, if not, use the default value
if [ -z "$1" ]; then
    echo "Using default image name: executor_container"
    imageName="executor_container"
else
    imageName="$1"
fi

imageName="$1"
taskweaverPath="../taskweaver"
requirementsPath="../requirements.txt"

if [ -d "$taskweaverPath" ]; then
    echo "Using local files from $taskweaverPath"
    cp -r "$taskweaverPath" .
    cp "$requirementsPath" .
else
    echo "Local files not found."
    exit 1
fi

# Build the Docker image
docker build -t "$imageName" .

rm -rf taskweaver
rm requirements.txt
