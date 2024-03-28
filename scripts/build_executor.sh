#!/bin/bash

# Get the directory containing the script file
scriptDirectory="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "The script directory is: $scriptDirectory"

version="0.1"
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
<<<<<<< HEAD:scripts/build_executor.sh
docker build -t "$imageFullName" -f "$dockerfilePath" "$contextPath"

# Tag the image
docker tag "$imageFullName" "$imageName:latest"
=======
docker build -t "$imageName" -f "$dockerfilePath" "$contextPath"

# Tag the image
docker tag "$imageName" taskweavercontainers/taskweaver-executor:latest
>>>>>>> 99f1803e9fa8d55c5c739b42baf35a2021d92db1:scripts/build.sh
