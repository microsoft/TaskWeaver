#!/bin/bash

if [ -z "$1" ]; then
    echo "Please provide an image name as an argument."
    exit 1
fi

imageName="$1"
taskweaverPath="../taskweaver"
requirementsPath="../requirements.txt"

if [ -d "$taskweaverPath" ]; then
    echo "Using local files from $folderPath"
    cp -r "$taskweaverPath" .
    cp "$requirementsPath" .
else
    echo "Cloning repository and using repository files"
    git clone https://github.com/microsoft/TaskWeaver.git
    mv ".TaskWeaver/taskweaver" .
    mv ".TaskWeaver/requirements.txt" .
    rm -rf ".TaskWeaver"
fi

# Build the Docker image
docker build -t "$imageName" .

rm -rf taskweaver
rm requirements.txt
