# Shared Git freeze gate for formal post-sixth-freeze training launchers.
#
# The formal protocol requires that any training script terminate when HEAD is
# not the frozen commit, when tracked source changes are uncommitted, or when
# untracked files exist outside the approved formal-results root. Only
# ``results/paper_config_runs/formal_budget_post_sixth_freeze_v1/**`` untracked
# files are tolerated; any other untracked file (e.g. sitecustomize.py, stray
# scripts) could silently alter runtime behaviour and is a BLOCKED condition.

$FormalFreezeTag = "formal-post-sixth-ops-v1.3.3"
$FormalResultsRoot = "results/paper_config_runs/formal_budget_post_sixth_freeze_v1_evidence_rerun_20260801"
# Allow legacy archive/preflight and corrupted-forensic directories.
$AllowedUntrackedPatterns = @(
    "$FormalResultsRoot/*",
    "results/paper_config_runs/formal_budget_post_sixth_freeze_v1_corrupted_forensic/*",
    "results/paper_config_runs/formal_budget_post_sixth_freeze_v1.2_single_bc_preflight/*",
    "results/paper_config_runs/formal_budget_post_sixth_freeze_v1_dev_archive/*",
    "results/paper_config_runs/formal_budget_post_sixth_freeze_v1_preflight/*",
    "results/paper_config_runs/formal_budget_post_sixth_freeze_preflight/*",
    "results/paper_config_runs/formal_budget_pre_sixth_freeze_development/*"
)

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

    # ---- Untracked-file whitelist ----
    # Only untracked files under the approved formal-results root (and its
    # recognized archive siblings) are tolerated. Any other untracked file
    # (e.g. a stray Python module, a temp script) could silently change
    # runtime behaviour and voids the formal-evidence claim.
    $untracked = @(& git ls-files --others --exclude-standard)
    $badUntracked = @(
        $untracked | Where-Object {
            $ok = $false
            foreach ($pat in $AllowedUntrackedPatterns) {
                if ($_ -like $pat) { $ok = $true; break }
            }
            -not $ok
        }
    )
    if ($badUntracked.Count -gt 0) {
        Write-Error "BLOCKED: untracked files outside the approved formal results root ($FormalResultsRoot) and its archive siblings:"
        $badUntracked | ForEach-Object { Write-Error "  $_" }
        Write-Error "Remove or .gitignore those files before formal runs."
        exit 2
    }

    Write-Host "Freeze gate OK: HEAD=$head tag=$ExpectedTag tracked tree clean, untracked whitelist OK"
    return $tagCommit
}
