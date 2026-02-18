# 一键安装 ECC + Superpowers 到本项目的 .cursor 目录
# 在 enterprise_rag 项目根目录执行: .\scripts\install-cursor-ecc-and-superpowers.ps1
# 或: cd e:\Super Fund\enterprise_rag; .\scripts\install-cursor-ecc-and-superpowers.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot | Split-Path -Parent
$EccRoot = Join-Path $ProjectRoot "..\everything-claude-code-main"
$SuperRoot = Join-Path $ProjectRoot "..\superpowers-main"
$CursorSrc = Join-Path $EccRoot ".cursor"
$Dest = Join-Path $ProjectRoot ".cursor"

Write-Host "Project root: $ProjectRoot"
Write-Host "Destination:  $Dest"
Write-Host ""

# ---------- 1. ECC ----------
if (-not (Test-Path $CursorSrc)) {
    Write-Warning "未找到 ECC .cursor 目录: $CursorSrc"
    Write-Warning "请确认 everything-claude-code-main 位于: $EccRoot"
} else {
    Write-Host "[1/3] Installing Everything Claude Code (ECC)..."

    $rulesSrc = Join-Path $CursorSrc "rules"
    if (Test-Path $rulesSrc) {
        New-Item -ItemType Directory -Force -Path (Join-Path $Dest "rules") | Out-Null
        Get-ChildItem $rulesSrc -Filter "common-*.md" -ErrorAction SilentlyContinue | Copy-Item -Destination (Join-Path $Dest "rules") -Force
        Get-ChildItem $rulesSrc -Filter "python-*.md" -ErrorAction SilentlyContinue | Copy-Item -Destination (Join-Path $Dest "rules") -Force
        Write-Host "  - rules -> .cursor/rules/"
    }

    foreach ($dir in @("agents","skills","commands")) {
        $srcDir = Join-Path $CursorSrc $dir
        if (Test-Path $srcDir) {
            $destDir = Join-Path $Dest $dir
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
            Copy-Item -Path (Join-Path $srcDir "*") -Destination $destDir -Recurse -Force
            Write-Host "  - $dir -> .cursor/$dir/"
        }
    }

    $mcpFile = Join-Path $CursorSrc "mcp.json"
    if (Test-Path $mcpFile) {
        Copy-Item $mcpFile -Destination (Join-Path $Dest "mcp.json") -Force
        Write-Host "  - mcp.json -> .cursor/mcp.json"
    }
    Write-Host "  ECC done."
    Write-Host ""
}

# ---------- 2. Superpowers skills ----------
$superSkillsSrc = Join-Path $SuperRoot "skills"
$superSkillsDest = Join-Path $Dest "skills\superpowers"
if (-not (Test-Path $superSkillsSrc)) {
    Write-Warning "未找到 Superpowers skills: $superSkillsSrc"
} else {
    Write-Host "[2/3] Installing Superpowers skills..."
    New-Item -ItemType Directory -Force -Path $superSkillsDest | Out-Null
    Copy-Item -Path (Join-Path $superSkillsSrc "*") -Destination $superSkillsDest -Recurse -Force
    Write-Host "  - skills -> .cursor/skills/superpowers/"
    Write-Host "  Superpowers skills done."
    Write-Host ""
}

# ---------- 3. Superpowers workflow rule ----------
$ruleContent = @"
# Superpowers 工作流（可选）

当用户提出新功能、大改或「帮忙规划/设计」时：
1. 先检查 `.cursor/skills/superpowers/` 下是否有适用技能（如 brainstorming、writing-plans、subagent-driven-development）。
2. 若适用，先读取对应 SKILL.md 并遵循其流程（例如先头脑风暴与设计确认，再拆任务与执行）。
3. 与 ECC 的规则与技能并存：可同时使用 ECC 的 plan、tdd、code-review 等能力。
"@
$rulePath = Join-Path $Dest "rules\superpowers-workflow.md"
New-Item -ItemType Directory -Force -Path (Join-Path $Dest "rules") | Out-Null
Set-Content -Path $rulePath -Value $ruleContent.Trim() -Encoding UTF8
Write-Host "[3/3] Created .cursor/rules/superpowers-workflow.md"
Write-Host ""

Write-Host "Done. Open this project in Cursor to use ECC + Superpowers."
Write-Host "See: docs/Cursor-ECC-Superpowers-安装方案.md for details."
