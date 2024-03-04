$scriptDirectory = $PSScriptRoot
Write-Host "The script directory is: $scriptDirectory"

$imageName = "taskweaver/executor"
$taskweaverPath = Join-Path -Path $scriptDirectory -ChildPath "..\taskweaver"
$dockerfilePath = Join-Path -Path $scriptDirectory -ChildPath "..\ces_container\Dockerfile"
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
docker build -t $imageName -f $dockerfilePath $contextPath

