#!/bin/bash

imageName="taskweaver/executor"
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
