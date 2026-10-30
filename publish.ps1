# Publie le trainer sur GitHub : build, aperçu de ce qui part, confirmation, commit, push.
# Lancement : double-clic sur publish.cmd (ou powershell -ExecutionPolicy Bypass -File .\publish.ps1)
# Prérequis : gh auth login (fait). Premier lancement : crée le repo public TGM-hub/indonesia-kabupaten
# et active GitHub Pages (branche main, racine). Relançable ensuite pour pousser les mises à jour.

$ErrorActionPreference = "Continue"   # PowerShell 5.1 : "Stop" rend fatal le stderr de git
$Repo = "TGM-hub/indonesia-kabupaten"
$Remote = "https://github.com/$Repo.git"
$Url = "https://tgm-hub.github.io/indonesia-kabupaten/"
Set-Location $PSScriptRoot
$env:PYTHONIOENCODING = "utf-8"

# 1. Build : on ne publie jamais une version cassée
# « python » peut être le raccourci du Microsoft Store : on garde le premier qui tourne vraiment
$Py = $null
foreach ($c in "py", "python", "python3") {
    if (Get-Command $c -ErrorAction SilentlyContinue) { & $c -c "import sys" *> $null; if ($LASTEXITCODE -eq 0) { $Py = $c; break } }
}
if ($Py) {
    & $Py build.py
    if ($LASTEXITCODE -ne 0) { throw "Build en erreur : corrige les fichiers signalés avant de publier." }
} else {
    Write-Host "Python introuvable : publication de index.html tel quel (déjà construit)." -ForegroundColor Yellow
}

# 2. Dépôt local (premier lancement)
if (-not (Test-Path ".git")) {
    git init -b main | Out-Null
    git remote add origin $Remote
    Write-Host "Dépôt initialisé, remote : $Remote"
}
git config core.quotepath false

# 3. Aperçu
git add -A
$staged = git diff --cached --name-status
$hasUpstream = git rev-parse --abbrev-ref "main@{upstream}" 2>$null
$ahead = if ($hasUpstream) { git rev-list --count "origin/main..main" } elseif (git rev-parse --verify -q HEAD) { "1" } else { "0" }
if (-not $staged -and $ahead -eq "0") { Write-Host "`nRien de nouveau à publier."; exit 0 }

if ($staged) {
    Write-Host "`nFichiers qui vont partir :" -ForegroundColor Cyan
    $staged | ForEach-Object { Write-Host "  $_" }
    $bytes = (git diff --cached --name-only | Where-Object { Test-Path -LiteralPath $_ } | ForEach-Object { (Get-Item -LiteralPath $_).Length } | Measure-Object -Sum).Sum
    Write-Host ("`n{0} fichier(s), {1:N1} Mo." -f @($staged).Count, ($bytes / 1MB))
} else {
    Write-Host "`nCommits locaux pas encore poussés :" -ForegroundColor Cyan
    git log --oneline -n 10
}
gh repo view $Repo *> $null
$repoExists = ($LASTEXITCODE -eq 0)
if (-not $repoExists) { Write-Host "Le repo $Repo n'existe pas encore : il sera créé en public." -ForegroundColor Yellow }
if ((Read-Host "Publier ? (o/N)") -notmatch '^[oOyY]') { git reset -q; Write-Host "Annulé, rien n'est parti."; exit 1 }

# 4. Repo GitHub (premier lancement)
if (-not $repoExists) {
    gh repo create $Repo --public --description "GeoGuessr trainer: the 514 kabupaten/kota of Indonesia" --homepage $Url
    if ($LASTEXITCODE -ne 0) { throw "gh repo create a échoué" }
}

# 5. Commit et push
if ($staged) {
    $msg = Read-Host ("Message de commit (Entrée = « Mise à jour {0:yyyy-MM-dd} »)" -f (Get-Date))
    if (-not $msg) { $msg = "Mise à jour {0:yyyy-MM-dd}" -f (Get-Date) }
    git commit -q -m $msg -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
    if ($LASTEXITCODE -ne 0) { throw "git commit a échoué" }
}
git push -u origin main
if ($LASTEXITCODE -ne 0) { throw "git push a échoué (voir le message ci-dessus)" }

# 6. GitHub Pages (premier lancement)
gh api "repos/$Repo/pages" *> $null
if ($LASTEXITCODE -ne 0) {
    gh api -X POST "repos/$Repo/pages" -f "source[branch]=main" -f "source[path]=/" | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "Active Pages à la main : Settings > Pages > main / root." -ForegroundColor Yellow }
}
Write-Host "`nPublié. En ligne d'ici une minute : $Url" -ForegroundColor Green
