param(
    [Parameter(Mandatory=$true)][string]$Role,
    [Parameter(Mandatory=$true)][string]$TaskId,
    [Parameter(Mandatory=$true)][string]$Slug
)

$Branch = "agent/$Role/$TaskId-$Slug"
$Worktree = "../project-$Role-$TaskId"

git fetch origin
if ($LASTEXITCODE -ne 0) { throw "git fetch failed" }

git worktree add $Worktree -b $Branch origin/main
if ($LASTEXITCODE -ne 0) { throw "git worktree add failed" }

Write-Host "Created:"
Write-Host "  branch:   $Branch"
Write-Host "  worktree: $Worktree"
