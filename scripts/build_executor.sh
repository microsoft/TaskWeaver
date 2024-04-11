#!/bin/bash

# Get the directory containing the script file
scriptDirectory="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "The script directory is: $scriptDirectory"

version="0.2"
imageName="taskweavercontainers/taskweaver-executor"
imageFullName="$imageName:$version"

taskweaverPath="$scriptDirectory/../taskweaver"
dockerfilePath="$scriptDirectory/../docker/ces_container/Dockerfile"
contextPath="$scriptDirectory/../"

if [ -d "$taskweaverPath" ]; then
    echo "Found module files from $taskweaverPath"
    echo "Dockerfile path: $dockerfilePath"
    echo "Context path: $contextPath"
else
    echo "Local files not found."
    exit 1
fi

# Build the Docker image
docker build -t "$imageFullName" -f "$dockerfilePath" "$contextPath"

# Tag the image
docker tag "$imageFullName" "$imageName:latest"
