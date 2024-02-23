param (
    [string]$imageName
)

if (-not $imageName) {
    Write-Host "Please provide an image name as an argument."
    exit 1
}

$taskweaverPath = "..\taskweaver"
$requirementsPath = "..\requirements.txt"

if (Test-Path $taskweaverPath) {
    Write-Host "Using local files from $taskweaverPath"
    Copy-Item -Path $taskweaverPath -Destination ".\taskweaver" -Recurse
    Copy-Item -Path $requirementsPath -Destination ".\requirements.txt"
} else {
    Write-Host "Local files not found."
    exit 1
}

# Build the Docker image
docker build -t $imageName .

# Remove temporary files
Remove-Item -Path ".\taskweaver" -Recurse -Force
Remove-Item -Path ".\requirements.txt" -Force
