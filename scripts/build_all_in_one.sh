#!/bin/bash

# Usage: ./script.sh --with-web-search=true
# Default value for with web search option
WithWebSearch=false

for i in "$@"
do
case $i in
    --with-web-search=*)
    WithWebSearch="${i#*=}"
    shift # past argument=value
    ;;
    *)
    # unknown option
    ;;
esac
done

scriptDirectory="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "The script directory is: $scriptDirectory"

version="0.2"
imageName="taskweavercontainers/taskweaver-all-in-one"

# Generate the image name with the web search option
if [ "$WithWebSearch" == "true" ]; then
    imageFullName="${imageName}:${version}-ws"
    latestImageName="${imageName}:latest-ws"
    echo '{"session.roles": ["planner", "code_interpreter", "web_search"]}' > "../docker/all_in_one_container/taskweaver_config.json"
else
    imageFullName="${imageName}:${version}"
    latestImageName="${imageName}:latest"
    echo '{"session.roles": ["planner", "code_interpreter"]}' > "../docker/all_in_one_container/taskweaver_config.json"
fi

taskweaverPath="$scriptDirectory/../taskweaver"
dockerfilePath="$scriptDirectory/../docker/all_in_one_container/Dockerfile"
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
docker build --build-arg WITH_WEB_SEARCH="$WithWebSearch" -t "$imageFullName" -f "$dockerfilePath" "$contextPath"

# Tag the image
docker tag "$imageFullName" "$latestImageName"
