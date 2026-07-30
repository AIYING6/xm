# Shared Git freeze gate for formal post-sixth-freeze training launchers.
#
# The formal protocol requires that any training script terminate when HEAD is
# not the frozen commit, or when tracked source changes are uncommitted. This
# file centralizes that check so the BC launcher and the PPO chunk launcher
# cannot drift apart.
#
# Untracked files (notably results/) are intentionally ignored: formal outputs
# are produced by the run itself. Tracked source/config changes are NOT ignored.

$FormalFreezeTag = "formal-post-sixth-freeze-v1.1"

function Get-FreezeCommit {
    param([string]$Tag = $FormalFreezeTag)
    $commit = (& git rev-list -n 1 $Tag 2>$null)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($commit)) {
        return ""
    }
    return $commit.Trim()
}

function Assert-FrozenWorkspace {
    <#
    .SYNOPSIS
        Terminate the caller unless HEAD == frozen tag commit and the tracked
        working tree is clean.
    .OUTPUTS
        The frozen commit SHA on success. Calls exit 2 on any violation.
    #>
    param(
        [string]$ExpectedTag = $FormalFreezeTag,
        [switch]$AllowUnfrozen
    )

    $head = (& git rev-parse HEAD 2>$null)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($head)) {
        Write-Error "BLOCKED: cannot resolve git HEAD; refusing to produce formal artifacts."
        exit 2
    }
    $head = $head.Trim()

    $tagCommit = Get-FreezeCommit -Tag $ExpectedTag
    if ([string]::IsNullOrWhiteSpace($tagCommit)) {
        Write-Error "BLOCKED: freeze tag '$ExpectedTag' not found; create and push it before formal runs."
        exit 2
    }

    if ($head -ne $tagCommit) {
        if ($AllowUnfrozen) {
            Write-Warning "UNFROZEN RUN: HEAD=$head expected=$tagCommit (outputs are NOT formal evidence)."
        }
        else {
            Write-Error "BLOCKED: HEAD=$head, expected tag commit=$tagCommit ($ExpectedTag). Checkout the freeze tag before formal runs."
            exit 2
        }
    }

    # Tracked, unstaged modifications.
    & git diff --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Error "BLOCKED: tracked working-tree changes exist; commit or stash before formal runs."
        exit 2
    }

    # Staged but uncommitted modifications.
    & git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Error "BLOCKED: staged but uncommitted changes exist; commit before formal runs."
        exit 2
    }

    Write-Host "Freeze gate OK: HEAD=$head tag=$ExpectedTag tracked tree clean"
    return $tagCommit
}
