"""
T0 全自动模拟真人测试 - 一键执行入口

执行前 T0 必读：T0_模拟真人测试角色_说明书_v2.md 第〇章「自我认知」

流程：
  1. 输出自我认知（我是谁、要干什么、怎么干）
  2. 前置检查：服务可用性、测试素材
  3. 执行六阶段测试（human_simulator）
  4. 生成完整测试报告（含错误、反馈、优化意见汇总）

运行：在 enterprise_rag 根目录
  python run_t0_full_auto.py [--url http://localhost:8501] [--headless]
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = PROJECT_ROOT.parent  # e:\Super Fund


def _load_project_cognition() -> str | None:
    """加载 T0 项目认知文档"""
    for base in (WORKSPACE_ROOT, PROJECT_ROOT):
        p = base / "T0_项目认知.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
    return None


def _print_t0_self_awareness() -> None:
    """输出 T0 自我认知（说明书第〇章）"""
    print("\n" + "=" * 60)
    print("T0 自我认知（执行前必读）")
    print("=" * 60)
    print("""
【我是谁】
  角色：模拟真人测试员（T0）
  职责：以真实用户视角端到端测试 Enterprise RAG 系统
  执行模式：全自动，具备本机权限

【要干什么】
  目标：一轮完整测试后，产出可供系统优化参考的完整测试报告
  覆盖：冷启动 → 认证 → 初次使用 → 核心 RAG → 日常操作 → 高级功能
  输出：错误记录、使用反馈、优化意见汇总（角色设定、工作内容、测试素材、系统体验）

【怎么干】
  入口：本脚本 run_t0_full_auto.py
  步骤：前置检查 → 执行 human_simulator → 汇总报告
  结束：产出 T0_完整测试报告_YYYYMMDD_HHMMSS.md
""")
    print("=" * 60 + "\n")

    # 输出项目认知
    cog = _load_project_cognition()
    if cog:
        print("[T0] 项目认知（T0_项目认知.md）")
        print("-" * 50)
        for line in cog.strip().split("\n")[:35]:  # 摘要：标题与前三章
            print(line)
        print("-" * 50)
        print("[T0] 项目认知加载完成，建立清晰认知后开始测试\n")
    else:
        print("[WARN] 未找到 T0_项目认知.md，将按默认认知执行\n")


def _check_service(url: str, timeout: int = 5) -> bool:
    """检查服务是否可达"""
    try:
        import urllib.request
        req = urllib.request.Request(url, method="HEAD")
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except Exception:
        return False


def _ensure_test_assets() -> bool:
    """确保测试素材存在：优先运行 测试素材/prepare_all_assets.py"""
    assets_dir = WORKSPACE_ROOT / "测试素材"
    prepare_script = assets_dir / "prepare_all_assets.py"
    if prepare_script.exists():
        print("[T0] 准备测试素材（测试素材/prepare_all_assets.py）...")
        r = subprocess.run(
            [sys.executable, str(prepare_script)],
            cwd=str(assets_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if r.returncode != 0:
            print(f"[WARN] 素材生成返回 {r.returncode}")
        else:
            print("[T0] 测试素材就绪")
        return True
    fixtures = PROJECT_ROOT / "tests" / "fixtures"
    prepare_script = fixtures / "prepare_test_assets.py"
    if prepare_script.exists():
        print("[T0] 准备测试素材（fixtures）...")
        subprocess.run([sys.executable, str(prepare_script)], cwd=str(PROJECT_ROOT), capture_output=True)
        print("[T0] 测试素材就绪")
    return True


REPORT_JSON = PROJECT_ROOT / "tests" / "e2e" / "human_simulator" / "human_simulator_report.json"
REPORT_MD = PROJECT_ROOT / "T0_完整测试报告.md"


def _run_human_simulator(base_url: str, headless: bool, *, resume: bool = False) -> Path | None:
    """执行 human_simulator，返回 JSON 报告路径。报告写入固定路径，覆盖旧报告。"""
    sim = PROJECT_ROOT / "tests" / "e2e" / "human_simulator" / "human_simulator.py"
    if not sim.exists():
        print("[ERROR] 未找到 human_simulator.py")
        return None
    cmd = [sys.executable, str(sim), "--url", base_url, "--output", str(REPORT_JSON)]
    if headless:
        cmd.append("--headless")
    if resume:
        cmd.append("--resume")
    print(f"[T0] 执行 human_simulator: {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if r.returncode != 0:
        print(f"[WARN] human_simulator 返回 {r.returncode}")
    return REPORT_JSON if REPORT_JSON.exists() else None


def _generate_full_report(json_path: Path) -> Path:
    """从 JSON 报告生成 T0_完整测试报告.md（固定路径，覆盖旧报告）"""
    for old in PROJECT_ROOT.glob("T0_完整测试报告_*.md"):
        old.unlink()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    out_md = REPORT_MD

    errors = data.get("errors", [])
    feedback = data.get("feedback", [])
    suggestions = data.get("suggestions", [])

    lines = [
        "# T0 完整测试报告",
        "",
        f"**生成时间**：{data.get('run_at', '')}",
        f"**耗时**：{data.get('duration_seconds', 0)} 秒",
        f"**Base URL**：{data.get('base_url', '')}",
        "",
        "---",
        "",
        "## 一、执行摘要",
        "",
        f"- 错误数：{len(errors)}",
        f"- 反馈数：{len(feedback)}",
        f"- 优化意见数：{len(suggestions)}",
        "",
        "---",
        "",
        "## 二、错误记录",
        "",
    ]
    if not errors:
        lines.append("（无）")
    else:
        for e in errors:
            line = f"- **{e.get('page', '')}** | {e.get('action', '')} | `{e.get('code', '')}`: {e.get('message', '')}"
            if e.get("screenshot_path"):
                line += f"\n  - 截图：{e.get('screenshot_path')}"
            lines.append(line)

    lines.extend([
        "",
        "---",
        "",
        "## 三、使用反馈",
        "",
    ])
    for f in feedback:
        lines.append(f"- **{f.get('page', '')}** | {f.get('action', '')} | 流畅{f.get('fluency',0)} 易用{f.get('usability',0)} 需改进{f.get('improvement_needed',0)} | {f.get('comment', '')}")

    lines.extend([
        "",
        "---",
        "",
        "## 四、优化意见汇总",
        "",
        "供 C0/X6 做系统优化参考。",
        "",
    ])
    by_cat: dict[str, list] = {}
    for s in suggestions:
        cat = s.get("category", "其他")
        by_cat.setdefault(cat, []).append(s)
    for cat in ["角色设定", "工作内容", "测试素材", "系统体验"]:
        if cat in by_cat:
            lines.append(f"### {cat}")
            lines.append("")
            for s in by_cat[cat]:
                lines.append(f"- **[{s.get('priority','')}]** {s.get('content','')}")
                lines.append(f"  - 触发场景：{s.get('context','')}")
            lines.append("")
    for cat, items in by_cat.items():
        if cat not in ["角色设定", "工作内容", "测试素材", "系统体验"]:
            lines.append(f"### {cat}")
            lines.append("")
            for s in items:
                lines.append(f"- **[{s.get('priority','')}]** {s.get('content','')}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*本报告由 T0 全自动测试生成*")

    out_md.write_text("\n".join(lines), encoding="utf-8")
    return out_md


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="T0 全自动模拟真人测试")
    parser.add_argument("--url", default="http://localhost:8501", help="前端 base URL")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--skip-check", action="store_true", help="跳过服务可用性检查")
    parser.add_argument("--resume", action="store_true", help="从上次断点接着执行（测试中断时使用）")
    args = parser.parse_args()

    _print_t0_self_awareness()

    if not args.skip_check:
        print("[T0] 检查服务可用性...")
        if not _check_service(args.url):
            print(f"[ERROR] 无法访问 {args.url}，请确保前端(8501)、后端(8000)已启动")
            sys.exit(1)
        print("[T0] 服务就绪")

    _ensure_test_assets()

    json_path = _run_human_simulator(args.url, args.headless, resume=args.resume)
    checkpoint = PROJECT_ROOT / "tests" / "e2e" / "human_simulator" / "t0_checkpoint.json"
    if not json_path:
        if checkpoint.exists():
            print("[T0] 测试已中断，断点已保存。下次运行加 --resume 从断点接着执行。")
        else:
            print("[ERROR] 未获得测试报告，退出")
        sys.exit(1)

    md_path = _generate_full_report(json_path)
    print(f"\n[T0] 完整测试报告已生成: {md_path}")
    print("[T0] 一轮测试结束")


if __name__ == "__main__":
    main()
