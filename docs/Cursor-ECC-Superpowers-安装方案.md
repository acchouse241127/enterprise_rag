# 在 Cursor 中安装 ECC 与 Superpowers 的可行性评估与方案

本文档针对在 **Cursor IDE** 中安装并整合以下两个 GitHub 项目进行评估，并给出在 **enterprise_rag** 项目中的具体安装与使用方案：

1. **everything-claude-code**（ECC）— 完整 Claude Code 配置集合（规则、技能、代理、命令等）
2. **superpowers** — 基于技能的可组合开发工作流（头脑风暴 → 计划 → 子代理执行）

---

## 一、可行性评估

### 1. Everything Claude Code (ECC)

| 维度       | 评估 | 说明 |
|------------|------|------|
| **Cursor 支持** | ✅ 官方支持 | 仓库内包含 `.cursor/` 目录，提供规则、技能、代理、命令、MCP 的 Cursor 适配版本 |
| **安装方式**   | ✅ 脚本化 | 提供 `install.sh --target cursor <语言>`，可安装到**当前目录**的 `.cursor/` |
| **与主项目匹配** | ✅ 匹配 | enterprise_rag 为 **Python**（FastAPI + Streamlit），ECC 提供 `python` 规则与 Python 相关技能（如 python-patterns、python-testing、django-* 等），可直接选用 |
| **Windows 兼容** | ⚠️ 需注意 | `install.sh` 为 Bash 脚本，在 Windows 上需通过 **Git Bash** 或 **WSL** 执行，或使用下文提供的 PowerShell 方案 |

**结论：可行性高，推荐安装。**

---

### 2. Superpowers

| 维度       | 评估 | 说明 |
|------------|------|------|
| **Cursor 支持** | ⚠️ 无官方适配 | 官方仅说明 Claude Code（插件市场）、Codex、OpenCode，未提供 Cursor 专用安装步骤 |
| **技能格式**   | ✅ 兼容 | 使用标准 `SKILL.md`（含 frontmatter），与 Cursor 的 `.cursor/skills/` 目录约定一致 |
| **整合方式**   | ✅ 可手动整合 | 将 Superpowers 的 `skills/` 复制到项目的 `.cursor/skills/superpowers/`，并通过一条 Cursor Rule 引导 AI 在适当时机读取并遵循对应技能 |
| **与 ECC 关系** | ✅ 可并存 | ECC 侧重单点能力（/plan、/tdd、/code-review 等）；Superpowers 侧重端到端流程（头脑风暴 → 计划 → 子代理执行）。两者可互补使用 |

**结论：可行性中高，需手动复制技能并配一条 Rule 以触发使用。**

---

### 3. 与 enterprise_rag 的契合度

- **技术栈**：Python + FastAPI + Streamlit + RAG。ECC 的 **python** 规则与 **python-testing**、**backend-patterns**、**security-review** 等技能可直接用于优化与继续开发。
- **开发流程**：若希望 AI 先做需求澄清、再拆任务、再按任务执行并做代码审查，可引入 Superpowers 的 **brainstorming**、**writing-plans**、**subagent-driven-development** 等技能，与 ECC 的 `/plan`、`/tdd`、`/code-review` 搭配使用。
- **冲突**：两者都含 TDD、代码审查、计划等主题，属于**能力重叠而非互斥**，可同时安装，由你在对话中按需选用（例如先走 Superpowers 流程，再用 ECC 的 `/code-review` 做单次审查）。

---

## 二、推荐安装方案

### 方案 A：仅安装 ECC（最小成本、立即可用）

适合：希望先提升 Cursor 内的代码规范、测试、安全与计划能力，暂不引入完整 Superpowers 流程。

**步骤：**

1. **在项目根目录执行 ECC 的 Cursor 安装（需 Bash 环境）**
   - 若已安装 **Git Bash** 或 **WSL**，在 `e:\Super Fund\enterprise_rag` 下执行：
     ```bash
     bash "../everything-claude-code-main/install.sh" --target cursor python
     ```
   - 若只有 **PowerShell**，可使用下文「附录：PowerShell 安装脚本」在 `enterprise_rag` 下执行，效果等价。

2. **验证**
   - 检查是否生成/更新：`enterprise_rag/.cursor/rules/`、`.cursor/skills/`、`.cursor/agents/`、`.cursor/commands/`（及可选的 `mcp.json`）。
   - 在 Cursor 中打开 enterprise_rag，开始对话时可提及「按本项目规则与技能开发」，观察是否引用到 ECC 的规则与技能。

3. **（可选）MCP**
   - 若需使用 ECC 自带的 MCP 配置，将 `everything-claude-code-main/.cursor/mcp.json` 复制到 `enterprise_rag/.cursor/mcp.json`，并按要求配置环境变量（如 `GITHUB_PERSONAL_ACCESS_TOKEN`）。

---

### 方案 B：ECC + Superpowers 一并安装（完整工作流）

适合：希望既有 ECC 的规则与单点能力，又有 Superpowers 的「先澄清需求 → 再计划 → 再执行」的流程。

**步骤：**

1. **先完成方案 A**，确保 `enterprise_rag/.cursor/` 下已有 ECC 的 rules、skills、agents、commands。

2. **复制 Superpowers 技能到项目**
   - 在项目根目录执行（PowerShell 示例）：
     ```powershell
     $dest = ".cursor/skills/superpowers"
     New-Item -ItemType Directory -Force -Path $dest
     Copy-Item -Path "..\superpowers-main\skills\*" -Destination $dest -Recurse -Force
     ```
   - 或手动将 `superpowers-main/skills/` 下所有子目录（如 `brainstorming`、`writing-plans`、`subagent-driven-development` 等）复制到 `enterprise_rag/.cursor/skills/superpowers/`。

3. **新增一条 Cursor Rule 以触发 Superpowers**
   - 在 `enterprise_rag/.cursor/rules/` 下新建文件，例如 `superpowers-workflow.md`，内容建议为：
     ```markdown
     # Superpowers 工作流（可选）

     当用户提出新功能、大改或「帮忙规划/设计」时：
     1. 先检查 `.cursor/skills/superpowers/` 下是否有适用技能（如 brainstorming、writing-plans、subagent-driven-development）。
     2. 若适用，先读取对应 SKILL.md 并遵循其流程（例如先头脑风暴与设计确认，再拆任务与执行）。
     3. 与 ECC 的规则与技能并存：可同时使用 ECC 的 /plan、/tdd、/code-review 等能力。
     ```
   - 这样 Cursor 在相关对话中会优先看到这条规则，从而去读取并应用 Superpowers 技能。

4. **验证**
   - 在 Cursor 中提出例如「我想加一个导出对话为 PDF 的功能，先帮我理清需求和方案」；
   - 观察 AI 是否会先走 brainstorming / writing-plans，再结合 ECC 的规则做实现与审查。

---

### 方案 C：仅安装 Superpowers（不用 ECC）

适合：只想要 Superpowers 的流程，不需要 ECC 的大量规则与命令。

- 在 `enterprise_rag` 下创建 `.cursor/skills/superpowers/`，复制 Superpowers 的 `skills/` 内容（同方案 B 第 2 步）。
- 添加与方案 B 第 3 步类似的 Rule，引导在「新功能/规划/设计」时使用 `.cursor/skills/superpowers/` 下的技能。
- 不运行 ECC 的 `install.sh`，也不复制 ECC 的 rules/agents/commands。

---

## 三、推荐选择与后续优化

- **优先推荐方案 B（ECC + Superpowers）**：  
  - 一次装好 ECC 的 Python 规则与技能，利于 enterprise_rag 的规范、测试与安全；  
  - 同时具备 Superpowers 的流程，便于做需求澄清与任务拆分，再配合 ECC 的 `/plan`、`/tdd`、`/code-review` 做执行与质量保障。

- **后续可做**：
  - 在 `.cursor/rules/` 中增加一条**项目专属规则**（如 `enterprise-rag-conventions.md`），写明本项目的技术栈（FastAPI、Streamlit、RAG、ChromaDB）、目录约定和常用命令，便于 AI 更贴合当前项目。
  - 若 ECC 的某些规则与团队习惯冲突，可在 `.cursor/rules/` 中覆盖或删减对应文件。
  - 按需从 ECC 的 `.cursor/commands/` 中挑选常用命令，在 Cursor 中通过自定义指令或说明引导使用（Cursor 的斜杠命令与 Claude Code 不完全一致，可做语义等价说明）。

---

## 四、附录：PowerShell 安装脚本（仅 ECC → Cursor）

在 **Windows 仅安装 PowerShell**、无法运行 Bash 时，可在 **以 `enterprise_rag` 为当前目录** 的 PowerShell 中执行下面脚本，实现与 `install.sh --target cursor python` 等效的安装（仅复制 ECC 的 .cursor 内容到当前项目）：

```powershell
# 在 enterprise_rag 目录下执行
$EccRoot = "..\everything-claude-code-main"
$CursorSrc = Join-Path $EccRoot ".cursor"
$Dest = ".cursor"

if (-not (Test-Path $CursorSrc)) {
    Write-Error "未找到 ECC .cursor 目录: $CursorSrc"
    exit 1
}

# Rules (common + python)
$rulesSrc = Join-Path $CursorSrc "rules"
if (Test-Path $rulesSrc) {
    New-Item -ItemType Directory -Force -Path "$Dest\rules" | Out-Null
    Get-ChildItem $rulesSrc -Filter "common-*.md" | Copy-Item -Destination "$Dest\rules" -Force
    Get-ChildItem $rulesSrc -Filter "python-*.md" | Copy-Item -Destination "$Dest\rules" -Force
    Write-Host "Installed rules -> $Dest/rules/"
}

# Agents
$agentsSrc = Join-Path $CursorSrc "agents"
if (Test-Path $agentsSrc) {
    Copy-Item -Path "$agentsSrc\*" -Destination "$Dest\agents" -Recurse -Force
    Write-Host "Installed agents -> $Dest/agents/"
}

# Skills
$skillsSrc = Join-Path $CursorSrc "skills"
if (Test-Path $skillsSrc) {
    Copy-Item -Path "$skillsSrc\*" -Destination "$Dest\skills" -Recurse -Force
    Write-Host "Installed skills -> $Dest/skills/"
}

# Commands
$commandsSrc = Join-Path $CursorSrc "commands"
if (Test-Path $commandsSrc) {
    Copy-Item -Path "$commandsSrc\*" -Destination "$Dest\commands" -Recurse -Force
    Write-Host "Installed commands -> $Dest/commands/"
}

# MCP（可选）
$mcpFile = Join-Path $CursorSrc "mcp.json"
if (Test-Path $mcpFile) {
    Copy-Item $mcpFile -Destination "$Dest\mcp.json" -Force
    Write-Host "Installed MCP config -> $Dest/mcp.json"
}

Write-Host "Done. ECC Cursor configs installed to $Dest/"
```

使用方式：在 PowerShell 中 `cd e:\Super Fund\enterprise_rag`，粘贴并执行上述脚本即可。

---

## 五、小结

| 项目          | 在 Cursor 中安装 | 与 enterprise_rag 配合 |
|---------------|------------------|-------------------------|
| **ECC**       | ✅ 可行（官方 .cursor + install 或 PowerShell 脚本） | ✅ 推荐安装 python 规则与技能，用于规范、测试、安全与计划 |
| **Superpowers** | ✅ 可行（手动复制 skills + 一条 Rule） | ✅ 可选，用于需求澄清与任务拆分流程 |
| **同时安装**  | ✅ 可行，无冲突   | 推荐方案 B：先 ECC 再复制 Superpowers 并加 Rule |

按上述方案在 Cursor 中安装并整合 ECC 与 Superpowers 后，即可在 enterprise_rag 上更规范地优化与继续开发；若你希望，我可以再根据你当前目录结构写一份「一键执行」的 PowerShell 脚本（含 ECC + Superpowers + Rule 创建）。
