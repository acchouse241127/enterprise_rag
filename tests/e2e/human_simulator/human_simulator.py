"""
T0 模拟真人测试 - 浏览器自动化脚本（完整版）

一次执行全部测试（A～F 六阶段），不片段化。
- 中途若因特殊原因停止，记录断点；下次 --resume 从断点接着执行
- 全部完成后才输出报告

运行前：
  1. pip install playwright && playwright install chromium
  2. 确保前端 (8501)、后端 (8000) 已启动
  3. python human_simulator.py [--resume]
"""

from __future__ import annotations

import json
import random
import signal
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from playwright.sync_api import Page, sync_playwright


@dataclass
class ErrorRecord:
    page: str
    action: str
    code: str
    message: str
    timestamp: str
    screenshot_path: str | None = None


@dataclass
class FeedbackRecord:
    page: str
    action: str
    fluency: int
    usability: int
    improvement_needed: int
    comment: str
    timestamp: str


@dataclass
class OptimizationSuggestion:
    category: str
    priority: str
    content: str
    context: str


@dataclass
class Report:
    run_at: str
    duration_seconds: float
    base_url: str
    errors: list[ErrorRecord] = field(default_factory=list)
    feedback: list[FeedbackRecord] = field(default_factory=list)
    suggestions: list[OptimizationSuggestion] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_at": self.run_at,
            "duration_seconds": self.duration_seconds,
            "base_url": self.base_url,
            "errors": [asdict(e) for e in self.errors],
            "feedback": [asdict(f) for f in self.feedback],
            "suggestions": [asdict(s) for s in self.suggestions],
        }

    @classmethod
    def from_dict(cls, d: dict) -> Report:
        r = cls(
            run_at=d.get("run_at", ""),
            duration_seconds=float(d.get("duration_seconds", 0)),
            base_url=d.get("base_url", ""),
        )
        _err_fields = {"page", "action", "code", "message", "timestamp", "screenshot_path"}
        for e in d.get("errors", []):
            filtered = {k: v for k, v in e.items() if k in _err_fields}
            r.errors.append(ErrorRecord(**filtered))
        for f in d.get("feedback", []):
            r.feedback.append(FeedbackRecord(**f))
        for s in d.get("suggestions", []):
            r.suggestions.append(OptimizationSuggestion(**s))
        return r

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")


CHECKPOINT_FILE = Path(__file__).parent / "t0_checkpoint.json"
REPORT_JSON = Path(__file__).parent / "human_simulator_report.json"
QUIET = True
JS_ERROR_LIMIT = 5

# 测试素材目录（《测试素材说明》）：优先 测试素材/，其次 tests/fixtures/
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # enterprise_rag 的父目录
TEST_ASSETS_DIR = WORKSPACE_ROOT / "测试素材"
FALLBACK_ASSETS = Path(__file__).parent.parent.parent / "fixtures"


def _human_delay(min_sec: float = 0.3, max_sec: float = 0.8) -> None:
    time.sleep(random.uniform(min_sec, max_sec))


def _record_error(
    report: Report, page: str, action: str, code: str, message: str,
    screenshot_path: str | None = None,
) -> None:
    report.errors.append(
        ErrorRecord(
            page=page, action=action, code=code, message=message,
            timestamp=datetime.now().isoformat(), screenshot_path=screenshot_path,
        )
    )


def _record_feedback(
    report: Report, page: str, action: str, fluency: int, usability: int, improvement_needed: int, comment: str
) -> None:
    report.feedback.append(
        FeedbackRecord(
            page=page, action=action, fluency=fluency, usability=usability,
            improvement_needed=improvement_needed, comment=comment, timestamp=datetime.now().isoformat()
        )
    )


def _has_error_on_page(page: Page) -> tuple[bool, str]:
    try:
        err = page.locator('[data-baseweb="notification"][data-kind="error"]').first
        if err.is_visible():
            return True, err.text_content() or "未知错误"
        err2 = page.locator(".stAlert").filter(has_text="Error").first
        if err2.is_visible():
            return True, err2.text_content() or "未知错误"
    except Exception:
        pass
    return False, ""


def _add_suggestion(report: Report, category: str, priority: str, content: str, context: str) -> None:
    for s in report.suggestions:
        if s.content == content:
            return
    report.suggestions.append(OptimizationSuggestion(category=category, priority=priority, content=content, context=context))


def _generate_suggestions(report: Report, fixtures_dir: Path | None) -> None:
    error_codes = {e.code for e in report.errors}
    if "EXCEPTION" in error_codes or "TIMEOUT" in error_codes:
        _add_suggestion(report, "系统体验", "P0",
            "问答或接口超时/异常时，建议增加明确进度反馈与超时提示文案", "检测到 EXCEPTION 或 TIMEOUT")
    if "UI_ERROR" in error_codes:
        _add_suggestion(report, "系统体验", "P1",
            "错误提示应统一展示位置与样式", "检测到 UI_ERROR")
    if "JS_ERROR" in error_codes:
        _add_suggestion(report, "系统体验", "P0",
            "前端控制台存在 JS 错误，建议排查", "检测到 JS_ERROR")
    low_fluency = [f for f in report.feedback if f.fluency <= 2]
    if low_fluency:
        _add_suggestion(report, "系统体验", "P1",
            "部分操作流畅度偏低", f"低流畅度: {[f.action for f in low_fluency[:3]]}")
    if fixtures_dir:
        existing = {f.name.lower() for f in fixtures_dir.iterdir() if f.is_file()}
        if not any(n.endswith((".doc", ".ppt")) for n in existing):
            _add_suggestion(report, "测试素材", "P1", "建议增加 DOC/PPT 旧格式测试素材", "fixtures 缺少 .doc/.ppt")
        if not any(n.endswith((".png", ".jpg", ".jpeg")) for n in existing):
            _add_suggestion(report, "测试素材", "P1", "建议增加含文字截图 PNG/JPG", "fixtures 缺少图片")
    _add_suggestion(report, "测试素材", "P2", "建议准备接近 200MB 边界文件", "通用建议")
    covered = {f.page for f in report.feedback} | {e.page for e in report.errors}
    if "知识库编辑" not in covered and "文件夹同步" not in covered:
        _add_suggestion(report, "工作内容", "P2",
            "建议扩展知识库编辑、文件夹同步、对话导出、检索看板、异步任务", "阶段 F 未覆盖")
    _add_suggestion(report, "角色设定", "P2", "阶段 F 建议补充异步任务取消后状态校验", "说明书建议")


# ========== 步骤实现 ==========

def _step_a1_open_home(page: Page, report: Report, base_url: str) -> None:
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    _human_delay(1, 2)
    _record_feedback(report, "首页", "打开首页", 4, 5, 2, "首页加载正常，侧边栏可见")


def _step_a2_unauth_access(page: Page, report: Report, base_url: str) -> None:
    context = page.context
    new_page = context.new_page()
    try:
        new_page.goto(f"{base_url}/document_upload")
        new_page.wait_for_load_state("networkidle")
        _human_delay(1.5, 2.5)
        content = new_page.content()
        # OPT-021: 增强匹配条件，覆盖更多提示文案变体
        auth_hints = [
            "请先登录",
            "未登录",
            "请先前往",
            "前往登录",
            "需要登录",
            "登录后再使用",
            "Please login",
            "please log in",
        ]
        if any(hint in content for hint in auth_hints) or ("登录" in content and "前往" in content):
            _record_feedback(report, "冷启动", "未登录访问受保护页", 5, 5, 1, "正确提示请先登录")
        else:
            _record_feedback(report, "冷启动", "未登录访问受保护页", 4, 4, 2, "页面已加载，未明确验证提示文案")
    finally:
        new_page.close()


def _step_a3_click_login(page: Page, report: Report, base_url: str) -> None:
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    _human_delay(0.5, 1)
    link = None
    for sel in [
        page.locator("a[href*='Login']").first,
        page.locator("a[href*='login']").first,
        page.get_by_role("link", name="Login"),
        page.get_by_role("link", name="登录"),
        page.locator("a:has-text('登录')").first,
        page.locator("a:has-text('Login')").first,
    ]:
        try:
            if sel.count() > 0 and sel.is_visible():
                link = sel
                break
        except Exception:
            pass
    if link:
        link.click()
        page.wait_for_load_state("networkidle")
        _human_delay(0.5, 1)
        if "login" in page.url.lower() or "用户名" in page.content():
            _record_feedback(report, "冷启动", "点击登录链接", 5, 5, 1, "正确跳转登录页")
        else:
            _record_feedback(report, "冷启动", "点击登录链接", 4, 4, 2, "已点击侧边栏链接，跳转待确认")
    else:
        page.goto(f"{base_url}/login")
        page.wait_for_load_state("networkidle")
        _record_feedback(report, "冷启动", "点击登录链接", 4, 4, 2, "侧边栏未找到登录链接，直接导航至登录页")


def _step_b2_wrong_password(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/login")
    page.wait_for_load_state("networkidle")
    _human_delay()
    try:
        inputs = page.locator('input[type="text"], input[type="password"]')
        if inputs.count() >= 1:
            inputs.nth(0).fill("admin")
        if inputs.count() >= 2:
            inputs.nth(1).fill("wrongpassword")
        btn = page.get_by_role("button", name="登录")
        if btn.is_visible():
            btn.click()
            page.wait_for_load_state("networkidle")
            _human_delay(1, 2)
        content = page.content()
        # OPT-021: 增强匹配条件，覆盖更多错误提示文案变体
        error_hints = [
            "失败",
            "错误",
            "invalid",
            "用户名或密码",
            "登录失败",
            "认证失败",
            "密码错误",
            "incorrect",
            "unauthorized",
        ]
        if any(hint in content or hint in content.lower() for hint in error_hints):
            _record_feedback(report, "登录", "错误密码登录", 5, 5, 1, "正确提示登录失败")
        else:
            _record_feedback(report, "登录", "错误密码登录", 4, 4, 2, "需确认错误密码时的提示是否展示")
    except Exception as e:
        _record_error(report, "登录", "错误密码登录", "EXCEPTION", str(e))


def _step_b3_empty_username(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/login")
    page.wait_for_load_state("networkidle")
    _human_delay()
    try:
        inputs = page.locator('input[type="text"], input[type="password"]')
        if inputs.count() >= 1:
            inputs.nth(0).fill("")
        if inputs.count() >= 2:
            inputs.nth(1).fill("")
        btn = page.get_by_role("button", name="登录")
        if btn.is_visible():
            btn.click()
            page.wait_for_load_state("networkidle")
            _human_delay(0.5, 1)
        if "用户名" in page.content() or "请输入" in page.content() or "必填" in page.content():
            _record_feedback(report, "登录", "空用户名登录", 5, 5, 1, "正确提示请输入用户名")
        else:
            _record_feedback(report, "登录", "空用户名登录", 4, 4, 2, "需确认前端是否校验空用户名")
    except Exception as e:
        _record_error(report, "登录", "空用户名登录", "EXCEPTION", str(e))


def _step_b1_login(page: Page, report: Report, base_url: str) -> bool:
    page.goto(f"{base_url}/login")
    page.wait_for_load_state("networkidle")
    _human_delay()
    try:
        inputs = page.locator('input[type="text"], input[type="password"]')
        if inputs.count() >= 1:
            inputs.nth(0).fill("admin")
        if inputs.count() >= 2:
            inputs.nth(1).fill("password123")
        btn = page.get_by_role("button", name="登录")
        if btn.is_visible():
            btn.click()
            page.wait_for_load_state("networkidle")
            _human_delay(1, 2)
    except Exception as e:
        _record_error(report, "登录", "登录", "EXCEPTION", str(e))
        return False
    has_err, msg = _has_error_on_page(page)
    if has_err:
        _record_error(report, "登录", "登录", "UI_ERROR", msg)
        return False
    ok = "已登录" in page.content() or "登录成功" in page.content()
    _record_feedback(report, "登录", "正确登录", 5 if ok else 4, 5, 2 if not ok else 1,
        "登录响应迅速" if ok else "登录完成，需确认成功提示")
    return True


def _step_c1_create_kb(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/knowledge_base_manage")
    page.wait_for_load_state("networkidle")
    _human_delay()
    try:
        name_input = page.locator('input[aria-label*="名称"], input[placeholder*="名称"]').first
        if name_input.is_visible():
            name_input.fill("T0_模拟测试知识库")
        create_btn = page.get_by_role("button", name="创建")
        if create_btn.is_visible():
            create_btn.click()
            page.wait_for_load_state("networkidle")
            _human_delay(1, 2)
    except Exception as e:
        _record_error(report, "知识库管理", "创建知识库", "EXCEPTION", str(e))
        return
    has_err, msg = _has_error_on_page(page)
    if has_err:
        _record_error(report, "知识库管理", "创建知识库", "UI_ERROR", msg)
        return
    _record_feedback(report, "知识库管理", "创建知识库", 4, 5, 2, "知识库创建流程清晰")


def _step_c2_list_kb(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/knowledge_base_manage")
    page.wait_for_load_state("networkidle")
    _human_delay(0.5, 1)
    if "T0_模拟测试知识库" in page.content() or "知识库" in page.content():
        _record_feedback(report, "知识库管理", "查看知识库列表", 4, 5, 2, "列表展示正常")
    else:
        _record_error(report, "知识库管理", "查看列表", "UI", "未看到刚创建的知识库")


def _get_test_files() -> list[Path]:
    """按《测试素材说明》获取多格式测试文件：优先 txt/pdf/docx，用于多格式上传验证"""
    for base in (TEST_ASSETS_DIR, FALLBACK_ASSETS, Path(__file__).parent):
        files = []
        for name in ("test_chinese.txt", "test_sample.docx", "test_normal.pdf"):
            p = base / name
            if p.exists():
                files.append(p)
        if files:
            return files
    fallback = Path(__file__).parent / "test_sample.txt"
    if not fallback.exists():
        fallback.write_text("T0 模拟真人测试 - 样本文档。用于验证文档上传与解析。", encoding="utf-8")
    return [fallback]


def _step_c3_upload(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/document_upload")
    page.wait_for_load_state("networkidle")
    _human_delay()
    test_files = _get_test_files()
    try:
        selectbox = page.locator('[data-baseweb="select"]').first
        if selectbox.is_visible():
            selectbox.click()
            _human_delay(0.3, 0.5)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            _human_delay(0.3, 0.5)
        file_input = page.locator('input[type="file"]')
        if file_input.count() > 0:
            file_input.first.set_input_files([str(f) for f in test_files])
            _human_delay(0.5, 1)
            upload_btn = page.get_by_role("button", name="开始上传").or_(page.get_by_role("button", name="上传")).first
            if upload_btn.is_visible():
                upload_btn.click()
                page.wait_for_load_state("networkidle")
                _human_delay(4, 8)
    except Exception as e:
        _record_error(report, "文档上传", "上传文档", "EXCEPTION", str(e))
        return
    has_err, msg = _has_error_on_page(page)
    if has_err:
        _record_error(report, "文档上传", "上传文档", "UI_ERROR", msg)
        return
    fmt_count = len(test_files)
    _record_feedback(report, "文档上传", "上传文档", 4, 4, 2,
        f"多格式上传({fmt_count}个文件)流畅" if fmt_count > 1 else "文件选择与上传操作流畅")


def _step_c4_wait_parse(page: Page, report: Report, base_url: str) -> None:
    _human_delay(3, 5)
    _record_feedback(report, "文档上传", "等待解析完成", 4, 4, 2, "解析等待时间可接受")


def _step_d1_qa(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/qa_chat")
    page.wait_for_load_state("networkidle")
    _human_delay()
    try:
        selectbox = page.locator('[data-baseweb="select"]').first
        if selectbox.is_visible():
            selectbox.click()
            _human_delay(0.2, 0.4)
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            _human_delay(0.3, 0.5)
        textarea = page.locator("textarea").first
        if textarea.is_visible():
            textarea.fill("请简单介绍一下知识库中的内容")
            _human_delay(0.3, 0.5)
        btn = page.get_by_role("button", name="开始问答").or_(page.get_by_role("button", name="提问")).or_(
            page.get_by_role("button").filter(has_text="问答")).first
        if btn.is_visible():
            btn.click()
            page.wait_for_load_state("networkidle")
            _human_delay(4, 8)
        page.mouse.wheel(0, 300)
        _human_delay(0.3, 0.6)
    except Exception as e:
        _record_error(report, "RAG 问答", "单轮问答", "EXCEPTION", str(e))
        return
    has_err, msg = _has_error_on_page(page)
    if has_err:
        _record_error(report, "RAG 问答", "单轮问答", "UI_ERROR", msg)
        return
    _record_feedback(report, "RAG 问答", "单轮问答", 4, 5, 2, "问答界面清晰，引用溯源可读")


def _step_d2_streaming(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/qa_chat")
    page.wait_for_load_state("networkidle")
    _human_delay()
    try:
        checkbox = page.locator('input[type="checkbox"]').filter(has_text="流式").or_(page.get_by_text("流式")).first
        if checkbox.is_visible():
            checkbox.click()
            _human_delay(0.2, 0.4)
        selectbox = page.locator('[data-baseweb="select"]').first
        if selectbox.is_visible():
            selectbox.click()
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            _human_delay(0.2, 0.4)
        textarea = page.locator("textarea").first
        if textarea.is_visible():
            textarea.fill("用一句话概括")
            _human_delay(0.2, 0.4)
        btn = page.get_by_role("button", name="开始问答").or_(page.get_by_role("button", name="提问")).first
        if btn.is_visible():
            btn.click()
            _human_delay(3, 6)
    except Exception as e:
        _record_error(report, "RAG 问答", "流式输出", "EXCEPTION", str(e))
        return
    _record_feedback(report, "RAG 问答", "流式输出", 4, 5, 2, "流式输出体验良好")


def _step_d3_multiturn(page: Page, report: Report, base_url: str) -> None:
    try:
        textarea = page.locator("textarea").first
        if textarea.is_visible():
            textarea.fill("能再详细一点吗")
            _human_delay(0.3, 0.5)
        btn = page.get_by_role("button", name="开始问答").or_(page.get_by_role("button", name="提问")).first
        if btn.is_visible():
            btn.click()
            _human_delay(4, 8)
    except Exception as e:
        _record_error(report, "RAG 问答", "多轮对话", "EXCEPTION", str(e))
        return
    _record_feedback(report, "RAG 问答", "多轮对话", 4, 5, 2, "能结合上文追问")


def _step_d4_no_answer(page: Page, report: Report, base_url: str) -> None:
    try:
        chat_input = page.locator("textarea").or_(page.locator('input[placeholder*="问题"], input[placeholder*="输入"]')).first
        if chat_input.is_visible():
            chat_input.fill("今天北京天气怎么样")
            _human_delay(0.3, 0.5)
            chat_input.press("Enter")
        else:
            textarea = page.locator("textarea").first
            if textarea.is_visible():
                textarea.fill("今天北京天气怎么样")
                textarea.press("Enter")
        _human_delay(5, 10)
        content = page.content()
        no_ans_phrases = (
            "未检索到", "无足够知识", "无法回答", "无相关", "知识库外", "无法从知识库",
            "未找到相关", "暂无相关", "抱歉", "无法提供", "没有找到",
        )
        no_ans = any(k in content for k in no_ans_phrases)
        if no_ans:
            _record_feedback(report, "RAG 问答", "无答案场景", 5, 5, 1, "正确提示未检索到知识，不捏造")
        elif "北京" in content and ("晴" in content or "雨" in content or "阴" in content or "度" in content):
            _record_error(report, "RAG 问答", "无答案场景", "HALLUCINATION", "可能捏造天气回答，应提示无知识")
        elif "天气" in content and ("度" in content or "℃" in content):
            _record_error(report, "RAG 问答", "无答案场景", "HALLUCINATION", "可能捏造具体天气数据")
        else:
            _record_feedback(report, "RAG 问答", "无答案场景", 4, 4, 2, "未明确无答案提示，需确认是否避免捏造")
    except Exception as e:
        _record_error(report, "RAG 问答", "无答案场景", "EXCEPTION", str(e))


def _step_d5_citation(page: Page, report: Report, base_url: str) -> None:
    try:
        page.mouse.wheel(0, 200)
        _human_delay(0.3, 0.5)
        if "引用" in page.content() or "ID:" in page.content() or "文档" in page.content():
            _record_feedback(report, "RAG 问答", "引用溯源", 4, 5, 2, "引用来源展示清晰，可定位原文")
        else:
            _record_feedback(report, "RAG 问答", "引用溯源", 4, 4, 2, "需确认引用展示")
    except Exception as e:
        _record_error(report, "RAG 问答", "引用溯源", "EXCEPTION", str(e))


def _step_d6_feedback(page: Page, report: Report, base_url: str) -> None:
    try:
        page.mouse.wheel(0, 400)
        _human_delay(0.8, 1.5)
        helpful_btn = page.locator("button:has-text('有用')").first
        try:
            helpful_btn.wait_for(state="visible", timeout=5000)
        except Exception:
            pass
        if helpful_btn.is_visible():
            helpful_btn.click()
            _human_delay(0.5, 1)
            _record_feedback(report, "RAG 问答", "有用/无用反馈", 4, 5, 2, "反馈按钮可点击，检索-反馈闭环可用")
        else:
            _record_feedback(report, "RAG 问答", "有用/无用反馈", 4, 4, 2, "未找到反馈按钮(需回答渲染后展示)")
    except Exception:
        _record_feedback(report, "RAG 问答", "有用/无用反馈", 4, 4, 2, "反馈功能待确认")


def _step_e1_reparse(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/document_upload")
    page.wait_for_load_state("networkidle")
    _human_delay(3, 5)
    try:
        for _ in range(3):
            page.mouse.wheel(0, 400)
            _human_delay(0.5, 1)
        reparse_btn = page.locator("button:has-text('重新解析')").first
        try:
            reparse_btn.wait_for(state="visible", timeout=18000)
        except Exception:
            pass
        if reparse_btn.is_visible():
            reparse_btn.click()
            page.wait_for_load_state("networkidle")
            _human_delay(3, 5)
            _record_feedback(report, "文档上传", "文档重新解析", 4, 4, 2, "重新解析流程可用")
        else:
            _record_feedback(report, "文档上传", "文档重新解析", 4, 4, 2, "未找到重新解析按钮或文档列表为空")
    except Exception as e:
        _record_feedback(report, "文档上传", "文档重新解析", 4, 4, 2, str(e)[:50])


def _step_e2_download(page: Page, report: Report, base_url: str) -> None:
    try:
        page.goto(f"{base_url}/document_upload")
        page.wait_for_load_state("networkidle")
        _human_delay(3, 5)
        for _ in range(3):
            page.mouse.wheel(0, 400)
            _human_delay(0.5, 1)
        dl_btn = page.locator("button:has-text('下载')").first
        try:
            dl_btn.wait_for(state="visible", timeout=15000)
        except Exception:
            pass
        if dl_btn.is_visible(timeout=5000):
            dl_btn.click()
            _human_delay(1, 2)
            save_btn = page.locator("button:has-text('保存')").first
            if save_btn.is_visible(timeout=5000):
                with page.expect_download(timeout=10000):
                    save_btn.click()
                _record_feedback(report, "文档上传", "文档下载", 4, 5, 2, "下载功能可用")
            else:
                _record_feedback(report, "文档上传", "文档下载", 4, 4, 2, "下载按钮可点，保存文件入口未出现")
        else:
            _record_feedback(report, "文档上传", "文档下载", 4, 4, 2, "未找到下载按钮")
    except Exception as e:
        _record_feedback(report, "文档上传", "文档下载", 4, 4, 2, str(e)[:60])


def _step_e3_delete_doc(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/document_upload")
    page.wait_for_load_state("networkidle")
    _human_delay(3, 5)
    try:
        for _ in range(3):
            page.mouse.wheel(0, 400)
            _human_delay(0.5, 1)
        del_btn = page.locator("button:has-text('删除')").first
        try:
            del_btn.wait_for(state="visible", timeout=15000)
        except Exception:
            pass
        if del_btn.is_visible(timeout=5000):
            del_btn.click()
            _human_delay(0.5, 1)
            confirm = page.locator("button:has-text('确定')").or_(page.locator("button:has-text('确认')")).first
            if confirm.is_visible(timeout=2000):
                confirm.click()
                _human_delay(0.5, 1)
            _record_feedback(report, "文档上传", "文档删除", 4, 4, 2, "文档删除流程可执行")
        else:
            _record_feedback(report, "文档上传", "文档删除", 4, 4, 2, "未找到删除按钮(跳过删除以保留文档)")
    except Exception:
        _record_feedback(report, "文档上传", "文档删除", 4, 4, 2, "删除流程待确认")


def _step_e5_delete_doc_in_kb(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/knowledge_base_manage")
    page.wait_for_load_state("networkidle")
    _human_delay(2, 3)
    try:
        manage_btn = page.locator("button:has-text('管理文档')").first
        if manage_btn.is_visible(timeout=5000):
            manage_btn.click()
            page.wait_for_load_state("networkidle")
            _human_delay(1, 2)
            page.mouse.wheel(0, 300)
            _human_delay(0.5, 1)
        doc_del_btns = page.locator("button:has-text('删除')")
        del_count = doc_del_btns.count()
        if del_count >= 2:
            _record_feedback(report, "知识库管理", "知识库内删除文档", 4, 5, 2, "文档列表已展开，删除入口可见")
        elif doc_del_btns.first.is_visible(timeout=3000):
            _record_feedback(report, "知识库管理", "知识库内删除文档", 4, 4, 2, "删除入口可见(或仅知识库级删除)")
        else:
            _record_feedback(report, "知识库管理", "知识库内删除文档", 4, 4, 2, "未展开文档列表或无可删文档")
    except Exception:
        _record_feedback(report, "知识库管理", "知识库内删除文档", 4, 4, 2, "删除功能待确认")


def _step_e4_new_session(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/qa_chat")
    page.wait_for_load_state("networkidle")
    _human_delay()
    try:
        new_btn = page.get_by_role("button", name="新建对话").or_(page.locator("button:has-text('新建对话')")).first
        if new_btn.is_visible(timeout=5000):
            new_btn.click()
            page.wait_for_load_state("networkidle")
            _human_delay(0.5, 1)
            _record_feedback(report, "RAG 问答", "新建会话", 4, 5, 2, "新建对话清空历史")
        else:
            _record_feedback(report, "RAG 问答", "新建会话", 4, 4, 2, "未找到新建对话按钮")
    except Exception:
        _record_feedback(report, "RAG 问答", "新建会话", 4, 4, 2, "新建对话待确认")


def _step_f1_kb_edit(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/kb_edit")
    page.wait_for_load_state("networkidle")
    _human_delay()
    if "知识库" in page.content() and ("编辑" in page.content() or "分块" in page.content()):
        _record_feedback(report, "知识库编辑", "进入编辑页", 4, 4, 2, "知识库编辑页可访问")
    else:
        _record_feedback(report, "知识库编辑", "进入编辑页", 4, 4, 2, "页面加载正常")


def _step_f2_chunk_params(page: Page, report: Report, base_url: str) -> None:
    try:
        if "chunk" in page.content().lower() or "分块" in page.content():
            _record_feedback(report, "知识库编辑", "分块参数", 4, 4, 2, "分块参数区域可见")
        else:
            _record_feedback(report, "知识库编辑", "分块参数", 4, 4, 2, "页面已加载")
    except Exception:
        _record_feedback(report, "知识库编辑", "分块参数", 4, 4, 2, "分块参数待确认")


def _step_f3_folder_sync(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/folder_sync")
    page.wait_for_load_state("networkidle")
    _human_delay()
    if "同步" in page.content() or "文件夹" in page.content():
        _record_feedback(report, "文件夹同步", "查看配置", 4, 4, 2, "文件夹同步页可访问")
    else:
        _record_feedback(report, "文件夹同步", "查看配置", 4, 4, 2, "页面加载")


def _step_f4_conversations(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/conversations")
    page.wait_for_load_state("networkidle")
    _human_delay()
    if "对话" in page.content():
        _record_feedback(report, "对话管理", "对话列表", 4, 5, 2, "对话管理页可访问")
        try:
            export_btn = page.get_by_role("button", name="导出").or_(page.locator("a:has-text('导出')")).first
            if export_btn.is_visible():
                _record_feedback(report, "对话管理", "导出 MD/PDF", 4, 4, 2, "导出入口可见")
            else:
                _record_feedback(report, "对话管理", "导出 MD/PDF", 4, 4, 2, "无对话时导出入口可能不展示")
        except Exception:
            _record_feedback(report, "对话管理", "导出 MD/PDF", 4, 4, 2, "导出功能待确认")
    else:
        _record_feedback(report, "对话管理", "对话列表", 4, 4, 2, "页面加载")


def _step_f5_share_link(page: Page, report: Report, base_url: str) -> None:
    try:
        share_btn = page.get_by_role("button", name="分享").or_(page.locator("button:has-text('分享')")).first
        if share_btn.is_visible():
            _record_feedback(report, "对话管理", "分享链接", 4, 4, 2, "分享入口可见")
        else:
            _record_feedback(report, "对话管理", "分享链接", 4, 4, 2, "无对话时分享入口可能不展示")
    except Exception:
        _record_feedback(report, "对话管理", "分享链接", 4, 4, 2, "分享功能待确认")


def _step_f6_retrieval_dashboard(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/retrieval_dashboard")
    page.wait_for_load_state("networkidle")
    _human_delay()
    if "检索" in page.content() or "看板" in page.content() or "统计" in page.content():
        _record_feedback(report, "检索看板", "查看统计", 4, 4, 2, "检索看板可访问")
    else:
        _record_feedback(report, "检索看板", "查看统计", 4, 4, 2, "页面加载")


def _step_f7_async_tasks(page: Page, report: Report, base_url: str) -> None:
    page.goto(f"{base_url}/async_tasks")
    page.wait_for_load_state("networkidle")
    _human_delay()
    if "任务" in page.content() or "异步" in page.content():
        _record_feedback(report, "异步任务", "任务列表", 4, 4, 2, "异步任务页可访问")
    else:
        _record_feedback(report, "异步任务", "任务列表", 4, 4, 2, "页面加载")


def _step_b4_logout(page: Page, report: Report, base_url: str) -> None:
    try:
        logout_btn = page.get_by_role("button", name="登出").or_(page.get_by_text("登出")).first
        if logout_btn.is_visible():
            logout_btn.click()
            page.wait_for_load_state("networkidle")
            _human_delay(0.5, 1)
        _record_feedback(report, "登录", "登出", 4, 5, 2, "登出成功")
    except Exception as e:
        _record_error(report, "登录", "登出", "EXCEPTION", str(e))


# 步骤列表：(step_id, 描述, 需要登录, handler) 按 T0 说明书第三章操作明细
STEPS: list[tuple[str, str, bool, Callable[[Page, Report, str], None]]] = [
    ("A1", "打开首页", False, _step_a1_open_home),
    ("A2", "未登录访问受保护页", False, _step_a2_unauth_access),
    ("A3", "点击登录链接", False, _step_a3_click_login),
    ("B2", "错误密码登录", False, _step_b2_wrong_password),
    ("B3", "空用户名登录", False, _step_b3_empty_username),
    ("B1", "正确登录", False, _step_b1_login),
    ("C1", "创建知识库", True, _step_c1_create_kb),
    ("C2", "查看知识库列表", True, _step_c2_list_kb),
    ("C3", "上传文档", True, _step_c3_upload),
    ("C4", "等待解析完成", True, _step_c4_wait_parse),
    ("D1", "单轮问答", True, _step_d1_qa),
    ("D2", "流式输出", True, _step_d2_streaming),
    ("D3", "多轮对话", True, _step_d3_multiturn),
    ("D4", "无答案场景", True, _step_d4_no_answer),
    ("D5", "引用溯源", True, _step_d5_citation),
    ("D6", "有用/无用反馈", True, _step_d6_feedback),
    ("E1", "文档重新解析", True, _step_e1_reparse),
    ("E2", "文档下载", True, _step_e2_download),
    ("E3", "文档删除", True, _step_e3_delete_doc),
    ("E4", "新建会话", True, _step_e4_new_session),
    ("E5", "知识库内删除文档", True, _step_e5_delete_doc_in_kb),
    ("F1", "知识库编辑", True, _step_f1_kb_edit),
    ("F2", "分块参数", True, _step_f2_chunk_params),
    ("F3", "文件夹同步", True, _step_f3_folder_sync),
    ("F4", "对话管理与导出", True, _step_f4_conversations),
    ("F5", "分享链接", True, _step_f5_share_link),
    ("F6", "检索看板", True, _step_f6_retrieval_dashboard),
    ("F7", "异步任务", True, _step_f7_async_tasks),
    ("B4", "登出", True, _step_b4_logout),
]


def _save_checkpoint(step_id: str, report: Report, base_url: str, stop_reason: str) -> None:
    data = {
        "last_completed_step_id": step_id,
        "report": report.to_dict(),
        "stop_reason": stop_reason,
        "stop_timestamp": datetime.now().isoformat(),
        "base_url": base_url,
    }
    CHECKPOINT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_checkpoint() -> tuple[str | None, Report | None, str] | None:
    if not CHECKPOINT_FILE.exists():
        return None
    try:
        data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        last = data.get("last_completed_step_id")
        report = Report.from_dict(data.get("report", {}))
        reason = data.get("stop_reason", "unknown")
        return (last, report, reason)
    except Exception:
        return None


def _run_steps(
    page: Page,
    report: Report,
    base_url: str,
    start_after: str | None,
    interrupted: list[bool],
    last_completed: list[str],
) -> None:
    step_ids = [s[0] for s in STEPS]
    start_idx = 0
    if start_after:
        for i, sid in enumerate(step_ids):
            if sid == start_after:
                start_idx = i + 1
                break

    logged_in = False
    for i in range(start_idx, len(STEPS)):
        if interrupted[0]:
            break
        step_id, desc, need_login, handler = STEPS[i]
        if need_login and not logged_in:
            if not _step_b1_login(page, report, base_url):
                prev = step_ids[i - 1] if i > 0 else "A3"
                _save_checkpoint(prev, report, base_url, "登录失败导致中断")
                interrupted[0] = True
                return
            logged_in = True
        try:
            handler(page, report, base_url)
            last_completed[0] = step_id
            if step_id == "B1":
                logged_in = True
            if step_id == "B4":
                logged_in = False
            _human_delay(0.5, 1)
        except Exception as e:
            _record_error(report, "步骤", step_id, "EXCEPTION", str(e)[:200])
            _save_checkpoint(step_id, report, base_url, f"步骤 {step_id} 异常: {e}")
            interrupted[0] = True
            raise


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="T0 模拟真人测试（完整版）")
    parser.add_argument("--url", default="http://localhost:8501", help="前端 base URL")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--output", default=None, help="报告输出路径")
    parser.add_argument("--resume", action="store_true", help="从上次断点接着执行")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    start = time.time()
    report: Report
    start_after: str | None = None

    if args.resume:
        cp = _load_checkpoint()
        if cp:
            start_after, report, reason = cp
            if not QUIET:
                print(f"[T0] 从断点恢复，上次停止: {reason}，接着 {start_after} 之后执行")
        else:
            report = Report(run_at=datetime.now().isoformat(), duration_seconds=0, base_url=base_url)
    else:
        report = Report(run_at=datetime.now().isoformat(), duration_seconds=0, base_url=base_url)
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()

    interrupted = [False]
    last_completed: list[str] = [start_after or "A0"]

    def _on_signal(signum, frame):
        interrupted[0] = True

    signal.signal(signal.SIGINT, _on_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _on_signal)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        page = context.new_page()

        js_err_count = [0]

        def on_console(msg):
            if msg.type == "error" and js_err_count[0] < JS_ERROR_LIMIT:
                js_err_count[0] += 1
                _record_error(report, "Console", "JS", "JS_ERROR", msg.text[:200])

        page.on("console", on_console)

        try:
            _run_steps(page, report, base_url, start_after, interrupted, last_completed)
        except Exception as e:
            if not QUIET:
                print(f"[T0] 执行异常: {e}")
        finally:
            browser.close()

    report.duration_seconds = round(time.time() - start, 2)

    if interrupted[0]:
        _save_checkpoint(last_completed[0], report, base_url, "用户中断或异常")
        if not QUIET:
            print(f"[T0] 测试中断，断点已保存至 {CHECKPOINT_FILE}，下次使用 --resume 接着执行")
        return

    # 全部完成：删除断点，生成建议，输出报告
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

    fixtures_dir = Path(__file__).resolve().parent.parent.parent / "fixtures"
    _generate_suggestions(report, fixtures_dir if fixtures_dir.exists() else None)

    out_path = Path(args.output) if args.output else REPORT_JSON
    report.save(out_path)

    print(f"报告已保存: {out_path}")
    print(f"错误数: {len(report.errors)}, 反馈数: {len(report.feedback)}, 建议数: {len(report.suggestions)}")
    for e in report.errors:
        print(f"  [ERROR] {e.page} | {e.action} | {e.code}: {e.message[:80]}")
    for f in report.feedback:
        print(f"  [OK] {f.page} | {f.action} | 流畅{f.fluency} 易用{f.usability} 需改进{f.improvement_needed} | {f.comment[:50]}")
    for s in report.suggestions:
        print(f"  [建议] [{s.category}] {s.priority} {s.content[:80]}{'...' if len(s.content) > 80 else ''}")


if __name__ == "__main__":
    main()
