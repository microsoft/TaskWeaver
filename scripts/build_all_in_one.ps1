param(
    [Parameter(Mandatory=$true)]
    [string]$WithWebSearch="false"
)

$scriptDirectory = $PSScriptRoot
Write-Host "The script directory is: $scriptDirectory"

$version = "0.2"
$imageName = "taskweavercontainers/taskweaver-all-in-one"
# generate the image name with the web search option


if ($WithWebSearch -eq "true") {
    $imageFullName = "${imageName}:${version}-ws"
    $latestImageName = "${imageName}:latest-ws"
    Set-Content -Path "..\docker\all_in_one_container\taskweaver_config.json" -Value '{"session.roles": ["planner", "code_interpreter", "web_search"]}'
} else {
    $imageFullName = "${imageName}:${version}"
    $latestImageName = "${imageName}:latest"
    Set-Content -Path "..\docker\all_in_one_container\taskweaver_config.json" -Value '{"session.roles": ["planner", "code_interpreter"]}'
}

$taskweaverPath = Join-Path -Path $scriptDirectory -ChildPath "..\taskweaver"
$dockerfilePath = Join-Path -Path $scriptDirectory -ChildPath "..\docker\all_in_one_container\Dockerfile"
$contextPath = Join-Path -Path $scriptDirectory -ChildPath "..\"

if (Test-Path $taskweaverPath) {
    Write-Host "Found module files from $taskweaverPath"
    Write-Host "Dockerfile path: $dockerfilePath"
    Write-Host "Context path: $contextPath"
} else {
    Write-Host "Local files not found."
    exit 1
}

# Build the Docker image
docker build --build-arg WITH_WEB_SEARCH=$WithWebSearch -t $imageFullName -f $dockerfilePath $contextPath

# Tag the image
docker tag $imageFullName $latestImageName
