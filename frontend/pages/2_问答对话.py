"""RAG question answering page."""

import json
import os
import re
import uuid

import requests
import streamlit as st

from feedback import err_business, err_network, err_timeout, loading, success_expired, success_msg
from operation_log import logged_get, logged_post

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# 问题完善度检查
MIN_QUESTION_LEN = 5

# 方案2：风格感知的 placeholder 与 hint
INPUT_PLACEHOLDERS = {
    "A": "【A 严谨】请提出有明确范围的问题，包含具体术语/条款/流程。例：「XX 条款如何规定」「某流程的具体步骤是什么」",
    "B": "【B 友好】像日常对话一样提问。可问概览（如「主要讲了什么」）、细节（如「如何做 XX」）或追问（如「能再详细点吗」）",
    "C": "【C 折中】建议包含具体主题或关键词。概览类（如「概括核心要点」）或具体类（如「XX 是什么」「如何做 XX」）均可",
}

HINT_TOO_SHORT = {
    "A": f"问题过短（建议至少 {MIN_QUESTION_LEN} 字）。A 风格下建议包含具体术语或条款名称，如「XX 条款如何规定」「某流程的步骤是什么」",
    "B": f"问题过短（建议至少 {MIN_QUESTION_LEN} 字）。B 风格下可自然提问，如「这些文档主要讲了什么」「如何上传文档」",
    "C": f"问题过短（建议至少 {MIN_QUESTION_LEN} 字）。C 风格下建议写清主题或关键词，如「XX 是什么」「概括核心要点」",
}

HINT_NO_SUBSTANCE = {
    "A": "请描述具体想了解的内容。A 风格建议包含条款名、流程名或数据类型，如「违约责任的原文是什么」",
    "B": "请描述您想了解的主题。B 风格可自然表达，如「介绍一下」「能举例吗」",
    "C": "请描述您想了解的具体主题或关键词，如「XX 是什么」「如何做 XX」",
}

SUCCESS_TIPS = {
    "A": "✅ 问题已满足要求。A 风格提示：问题越具体，回答越准确、越易溯源",
    "B": "✅ 问题已满足要求。B 风格支持多轮追问，可继续补充或追问",
    "C": "✅ 问题已满足要求。C 风格在准确与可读之间平衡，可点击「确认提问」",
}


def _normalize_prompt_version(v: str | None) -> str:
    """返回 A/B/C 之一，无效则默认 C。"""
    if not v or not isinstance(v, str):
        return "C"
    u = v.strip().upper()
    return u if u in ("A", "B", "C") else "C"


def _check_question_complete(
    text: str,
    is_follow_up: bool = False,
    prompt_version: str = "C",
) -> tuple[bool, str]:
    """
    检查问题是否满足完善度要求。
    is_follow_up: 追问轮豁免 5 字限制（TC-QACONF-011）。
    prompt_version: 回答风格 A/B/C，用于返回风格化提示（方案2）。
    返回 (是否通过, 不通过时的提示信息)。
    """
    t = (text or "").strip()
    without_spaces = re.sub(r"\s+", "", t)
    version = _normalize_prompt_version(prompt_version)

    if not without_spaces:
        return False, HINT_NO_SUBSTANCE[version]
    if not re.search(r"[\w\u4e00-\u9fff]", t):
        return False, HINT_NO_SUBSTANCE[version]
    if not is_follow_up and len(t) < MIN_QUESTION_LEN:
        return False, HINT_TOO_SHORT[version]
    return True, ""


def build_headers() -> dict:
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _get_token() -> str:
    return st.session_state.get("access_token", "")


def check_auth() -> bool:
    """Check if user is authenticated."""
    if not st.session_state.get("access_token"):
        st.warning("⚠️ 请先登录后再使用此功能")
        st.page_link("pages/1_登录.py", label="前往登录", icon="🔐")
        return False
    return True


@st.cache_data(ttl=8, show_spinner=False)
def fetch_knowledge_bases(token: str) -> list[dict]:
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = logged_get(f"{API_BASE_URL}/knowledge-bases", headers=headers, timeout=12, operation_name="knowledge-bases.list")
        if resp.status_code == 401:
            return []
        data = resp.json()
        if data.get("code") != 0:
            return []
        return data.get("data", [])
    except Exception:
        return []


def render_citations(citations: list[dict]) -> None:
    if not citations:
        st.info("📝 本次回答未返回引用来源")
        return
    st.subheader("📚 引用来源")
    for item in citations:
        with st.container(border=True):
            st.markdown(
                f"**[ID:{item.get('id')}]** "
                f"文档 ID: {item.get('document_id')} | "
                f"片段: {item.get('chunk_index')}"
            )
            content_preview = item.get("content_preview") or ""
            if content_preview:
                st.caption(f"📄 {content_preview[:200]}{'...' if len(content_preview) > 200 else ''}")


def fetch_document_preview(doc_id: int) -> str | None:
    """获取文档全文预览内容。"""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/documents/{doc_id}/preview",
            headers=build_headers(),
            timeout=30,
            operation_name="documents.preview",
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("content", "")
    except Exception:
        pass
    return None


def _sanitize_download_filename(name: str, fallback: str = "download") -> str:
    """清理下载文件名：去掉路径、非法字符，限制长度。"""
    if not name or not name.strip():
        return fallback
    # 只保留文件名部分，去掉路径
    base = name.strip().replace("\\", "/").split("/")[-1]
    # 去掉可能影响保存的字符
    base = re.sub(r'[<>:"|?*\x00-\x1f]', "_", base)
    return base[:200] if len(base) > 200 else base or fallback


def fetch_document_download(doc_id: int, fallback_filename: str = "download") -> tuple[bytes | None, str]:
    """获取文档下载内容，返回 (bytes, filename)。避免把后端错误 JSON 当文件保存。"""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/documents/{doc_id}/download",
            headers=build_headers(),
            timeout=60,
            operation_name="documents.download",
        )
        if resp.status_code != 200:
            return None, ""
        # 后端错误有时会返回 200 + JSON，若当成文件保存会得到空白/乱码
        content_type = (resp.headers.get("Content-Type") or "").lower()
        if "application/json" in content_type:
            return None, ""
        content = resp.content
        if content is None or len(content) == 0:
            return None, ""
        filename = fallback_filename
        cd = resp.headers.get("Content-Disposition")
        if cd and "filename=" in cd:
            m = re.search(r'filename[*]?=(?:UTF-8\'\')?"?([^";\n]+)"?', cd)
            if m:
                filename = m.group(1).strip().strip('"')
        return content, filename or fallback_filename
    except Exception:
        pass
    return None, ""


def render_retrieved_chunks(chunks: list[dict]) -> None:
    """展示检索结果（含来源文件名），提供预览与下载，便于查阅。"""
    if not chunks:
        return
    st.subheader("📋 检索结果（按来源文件）")
    for i, item in enumerate(chunks):
        filename = item.get("filename") or "未知文件"
        doc_id = item.get("document_id")
        content = item.get("content") or ""
        preview = item.get("content_preview") or content[:300]
        with st.container(border=True):
            st.markdown(f"**来源文件：{filename}**" + (f"（文档 ID: {doc_id}）" if doc_id else ""))
            st.caption(f"片段索引: {item.get('chunk_index', '-')}")

            # 预览、下载按钮（仅当有 document_id 时可用）
            if doc_id is not None:
                col_preview, col_download, _ = st.columns([1, 1, 3])
                with col_preview:
                    if st.button("👁️ 预览全文", key=f"qa_preview_{i}_{doc_id}", use_container_width=True):
                        full_content = fetch_document_preview(doc_id)
                        if full_content is not None:
                            st.session_state[f"qa_preview_content_{doc_id}"] = full_content
                        else:
                            st.warning("无法获取预览")
                with col_download:
                    dl_cache_key = f"qa_dl_{doc_id}"
                    # 点击「下载文件」时拉取并写入 session_state，不 rerun，本轮即可显示「保存文件」
                    if dl_cache_key not in st.session_state:
                        if st.button("📥 下载文件", key=f"qa_dl_btn_{i}_{doc_id}", use_container_width=True):
                            with loading("准备下载..."):
                                dl_bytes, dl_name = fetch_document_download(doc_id, fallback_filename=filename)
                                if dl_bytes and len(dl_bytes) > 0:
                                    safe_name = _sanitize_download_filename(dl_name or filename, "download")
                                    st.session_state[dl_cache_key] = (dl_bytes, safe_name)
                                else:
                                    err_business("下载失败：未获取到文件内容")
                    # 已有缓存或本轮刚写入：显示「保存文件」按钮（同一轮内可见，减少 rerun 导致下载不触发）
                    if dl_cache_key in st.session_state:
                        dl_bytes, dl_name = st.session_state[dl_cache_key]
                        if dl_bytes and len(dl_bytes) > 0:
                            safe_name = _sanitize_download_filename(dl_name or filename, "download")
                            st.download_button(
                                label="💾 保存文件",
                                data=dl_bytes,
                                file_name=safe_name,
                                mime="application/octet-stream",
                                key=f"qa_save_{i}_{doc_id}",
                                use_container_width=True,
                            )
                        else:
                            st.caption("下载数据无效")

            # 展示片段内容（保持原文，避免编码问题）
            display_text = preview if len(content) <= 500 else preview + "\n\n... (已截断)"
            st.text_area(
                "内容",
                value=display_text,
                height=120,
                disabled=True,
                key=f"retrieved_chunk_{i}",
                label_visibility="collapsed",
            )

            # 若已点击过预览，展示全文
            preview_key = f"qa_preview_content_{doc_id}"
            if doc_id is not None and preview_key in st.session_state:
                st.divider()
                st.markdown("**📖 文档全文预览**")
                full_text = st.session_state[preview_key]
                if len(full_text) > 4000:
                    full_text = full_text[:4000] + "\n\n... (已截断，共 {} 字)".format(len(st.session_state[preview_key]))
                st.text_area("全文", value=full_text, height=280, disabled=True, key=f"qa_preview_area_{i}_{doc_id}", label_visibility="collapsed")
                if st.button("关闭预览", key=f"qa_close_preview_{i}_{doc_id}"):
                    del st.session_state[preview_key]
                    st.rerun()


# ========== 侧边栏（按 R4 规范） ==========
with st.sidebar:
    st.title("🏠 Enterprise RAG")
    
    # 用户信息
    username = st.session_state.get("username", "用户")
    st.markdown(f"👤 **{username}**")
    if st.button("🚪 登出", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # 知识库选择
    with loading("加载知识库列表..."):
        kb_items = fetch_knowledge_bases(_get_token())
    
    if kb_items:
        kb_map = {f"📁 {item['name']}": item["id"] for item in kb_items}
        selected_label = st.selectbox("📚 选择知识库", options=list(kb_map.keys()))
        selected_kb_id = kb_map[selected_label]
    else:
        selected_kb_id = None
    
    st.divider()
    
    # 新建对话
    if st.button("➕ 新建对话", type="primary", use_container_width=True):
        st.session_state["qa_conversation_id"] = uuid.uuid4().hex[:12]
        st.session_state.pop("qa_last_result", None)
        st.session_state.pop("qa_last_question", None)
        st.session_state.pop("qa_chat_history", None)
        st.rerun()
    
    # 设置区域
    with st.expander("⚙️ 问答设置"):
        top_k = st.slider(
            "检索 TopK",
            min_value=1,
            max_value=10,
            value=5,
            help=(
                "每次提问时，从知识库中取几条最相关的文档片段来生成答案。\n\n"
                "如何选择：\n"
                "• 问题很具体（如「某条款怎么规定」）→ 3～5 即可，速度快\n"
                "• 问题较宽（如「概括全部要点」）→ 5～8，信息更全\n"
                "• 知识库内容杂、容易有无关信息 → 偏低（3～5）减少干扰\n"
                "• 追求回答完整、宁可慢一点 → 偏高（6～8）\n"
                "• 追求速度、节省算力 → 偏低（3～5）\n\n"
                "默认 5 是平衡之选，一般够用。"
            ),
        )
        history_turns = st.slider("历史轮数", min_value=1, max_value=10, value=4, help="多轮问答时保留的历史轮数")
        stream_mode = st.checkbox("流式输出", value=True, help="实时显示生成内容")
        prompt_version = st.selectbox(
            "回答风格",
            options=["A", "B", "C"],
            index=2,
            format_func=lambda x: {"A": "A 严谨（偏安全）", "B": "B 友好（偏体验）", "C": "C 折中（默认）"}[x],
            help="A：严格约束，偏原文引用；B：清晰易懂，多轮友好；C：平衡准确与可读",
        )
    
    st.divider()
    st.caption("💬 对话 | 📚 知识库 | 📄 文档")

# ========== 主内容区 ==========
if not check_auth():
    st.stop()

if not kb_items or selected_kb_id is None:
    st.warning("📭 暂无知识库，请先到「知识库管理」页面创建并上传文档")
    col1, col2 = st.columns(2)
    with col1:
        st.page_link("pages/3_知识库管理.py", label="创建知识库", icon="📚")
    with col2:
        st.page_link("pages/4_文档上传.py", label="上传文档", icon="📄")
    st.stop()

# 获取当前知识库名称
current_kb_name = next((item["name"] for item in kb_items if item["id"] == selected_kb_id), "知识库")
st.header(f"💬 与「{current_kb_name}」对话")

if "qa_conversation_id" not in st.session_state:
    st.session_state["qa_conversation_id"] = uuid.uuid4().hex[:12]
conversation_id = st.session_state["qa_conversation_id"]

# 初始化聊天历史
if "qa_chat_history" not in st.session_state:
    st.session_state["qa_chat_history"] = []

# 显示聊天历史
for idx, msg in enumerate(st.session_state["qa_chat_history"]):
    with st.chat_message(msg["role"]):
        content = msg["content"]
        # OPT-017: 无答案场景用醒目提示
        if msg["role"] == "assistant" and (content.startswith("未检索到") or (not msg.get("citations") and "无法给出" in content)):
            st.warning(content)
        else:
            st.markdown(content)
        if msg["role"] == "assistant":
            # 引用来源
            if msg.get("citations"):
                with st.expander("📚 引用来源"):
                    for cite in msg["citations"]:
                        st.caption(f"📄 文档 ID: {cite.get('document_id')} | 片段: {cite.get('chunk_index')}")
            
            # Phase 3.2: 用户反馈按钮
            log_id = msg.get("retrieval_log_id")
            if log_id and not msg.get("feedback_given"):
                col_fb1, col_fb2, col_fb_spacer = st.columns([1, 1, 4])
                with col_fb1:
                    if st.button("👍 有用", key=f"fb_helpful_{idx}_{log_id}", use_container_width=True, help="点击反馈此回答有用"):
                        try:
                            resp = logged_post(
                                f"{API_BASE_URL}/retrieval/feedback",
                                json={"retrieval_log_id": log_id, "feedback_type": "helpful"},
                                headers=build_headers(),
                                timeout=10,
                                operation_name="retrieval.feedback.add",
                            )
                            if resp.json().get("code") == 0:
                                success_msg("感谢您的反馈！")
                                st.session_state["qa_chat_history"][idx]["feedback_given"] = True
                                st.rerun()
                        except Exception as e:
                            err_business(str(e))
                with col_fb2:
                    if st.button("👎 无用", key=f"fb_not_helpful_{idx}_{log_id}", use_container_width=True, help="点击反馈此回答无用"):
                        try:
                            resp = logged_post(
                                f"{API_BASE_URL}/retrieval/feedback",
                                json={"retrieval_log_id": log_id, "feedback_type": "not_helpful"},
                                headers=build_headers(),
                                timeout=10,
                                operation_name="retrieval.feedback.add",
                            )
                            if resp.json().get("code") == 0:
                                success_msg("感谢您的反馈！")
                                st.session_state["qa_chat_history"][idx]["feedback_given"] = True
                                st.rerun()
                        except Exception as e:
                            err_business(str(e))
            elif msg.get("feedback_given"):
                st.caption("✅ 已提交反馈")

# 聊天输入：两阶段（输入 → 完善提示 → 确认提问）；TC-QACONF-012 未通过时禁用按钮
# 使用计数器 key，避免提交后直接写 session_state 导致 "cannot be modified after widget instantiated"
if "_qa_input_counter" not in st.session_state:
    st.session_state["_qa_input_counter"] = 0
st.markdown("#### 输入问题")
_qa_key = f"qa_question_text_{st.session_state['_qa_input_counter']}"
_placeholder = INPUT_PLACEHOLDERS.get(_normalize_prompt_version(prompt_version), INPUT_PLACEHOLDERS["C"])
question = st.text_area(
    "问题内容",
    height=100,
    placeholder=_placeholder,
    label_visibility="collapsed",
    key=_qa_key,
)
# 追问豁免（TC-QACONF-011）：已有对话轮次时短句可提交
history = st.session_state.get("qa_chat_history", [])
is_follow_up = any(m.get("role") == "assistant" for m in history)
ok, hint = _check_question_complete(question or "", is_follow_up=is_follow_up, prompt_version=prompt_version)
col_confirm, col_optimize, col_hint = st.columns([1, 1, 2])
with col_hint:
    if question and question.strip():
        if not ok:
            st.caption(f"⚠️ {hint}")
        else:
            _tip = SUCCESS_TIPS.get(_normalize_prompt_version(prompt_version), SUCCESS_TIPS["C"])
            st.caption(_tip)
with col_confirm:
    submitted = st.button("确认提问", type="primary", disabled=not ok, use_container_width=True)
with col_optimize:
    optimize_clicked = st.button("✨ 提示词优化", type="secondary", use_container_width=True, help="获取当前风格下的提问优化建议")

# 提示词优化：点击后展示风格化建议
if optimize_clicked or st.session_state.get("qa_show_optimize"):
    st.session_state["qa_show_optimize"] = True
    ver = _normalize_prompt_version(prompt_version)
    with st.container(border=True):
        st.markdown("**✨ 提示词优化建议**")
        if ver == "A":
            st.markdown("**A 严谨风格**：问题越具体越好。")
            st.caption("✅ 推荐：含具体条款、流程、数值的问题，如「XX 条款如何规定」「某流程的步骤是什么」")
            st.caption("❌ 避免：过于宽泛的「介绍一下」「有哪些」")
        elif ver == "B":
            st.markdown("**B 友好风格**：自然对话即可。")
            st.caption("✅ 推荐：概览（「主要讲了什么」）、细节（「如何做 XX」）、追问（「能再详细点吗」）")
            st.caption("💡 多轮追问可用短句，如「详细点」「第一点呢」")
        else:
            st.markdown("**C 折中风格**：兼顾具体与可读。")
            st.caption("✅ 推荐：概览类或具体类均可，如「概括核心要点」「XX 是什么」「如何做 XX」")
            st.caption("💡 关键信息写清即可")
        if st.button("关闭", key="qa_close_optimize"):
            st.session_state.pop("qa_show_optimize", None)
            st.rerun()

submit = submitted and question is not None and (question.strip() or "")
if submitted and (not question or not question.strip()):
    st.error("请输入问题内容")
    submit = False
if submit:
    question = (question or "").strip()
    ok, hint = _check_question_complete(question, is_follow_up=is_follow_up, prompt_version=prompt_version)
    if not ok:
        st.error(hint)
        st.stop()

# 处理用户输入（仅在确认提问且通过完善度检查时）
if submit:
    cleaned_question = (question or "").strip()
    
    # 添加用户消息到历史
    st.session_state["qa_chat_history"].append({"role": "user", "content": cleaned_question})
    
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(cleaned_question)

    payload = {
        "knowledge_base_id": selected_kb_id,
        "question": cleaned_question,
        "top_k": top_k,
        "conversation_id": conversation_id,
        "history_turns": history_turns,
        "system_prompt_version": prompt_version,
    }
    headers = build_headers()

    # 显示助手回复（使用 chat_message 组件）
    with st.chat_message("assistant"):
        if not stream_mode:
            with st.spinner("正在思考中..."):
                try:
                    resp = logged_post(
                        f"{API_BASE_URL}/qa/ask",
                        json=payload,
                        headers=headers,
                        timeout=120,
                        operation_name="qa.ask",
                    )
                    if resp.status_code == 401:
                        success_expired()
                        del st.session_state["access_token"]
                        st.rerun()
                    data = resp.json()
                except requests.exceptions.ConnectionError:
                    err_network()
                    data = None
                except requests.exceptions.Timeout:
                    err_timeout()
                    data = None
                except Exception as exc:  # noqa: BLE001
                    err_business(f"请求失败：{exc}")
                    data = None

                if data:
                    if data.get("code") != 0:
                        st.error(data.get("detail") or data.get("message") or "问答失败")
                    else:
                        body = data["data"]
                        answer = body.get("answer", "")
                        citations = body.get("citations", [])
                        retrieval_log_id = body.get("retrieval_log_id")  # Phase 3.2
                        # OPT-017: 无答案场景用醒目提示
                        if answer.startswith("未检索到") or (not citations and "无法给出" in answer):
                            st.warning(answer)
                        else:
                            st.markdown(answer)
                        if citations:
                            with st.expander("📚 引用来源"):
                                for cite in citations:
                                    st.caption(f"📄 文档 ID: {cite.get('document_id')} | 片段: {cite.get('chunk_index')}")
                        # 添加到历史
                        st.session_state["qa_chat_history"].append({
                            "role": "assistant",
                            "content": answer,
                            "citations": citations,
                            "retrieval_log_id": retrieval_log_id,  # Phase 3.2
                        })
                        st.session_state["_qa_input_counter"] = st.session_state.get("_qa_input_counter", 0) + 1  # 清空输入框
                        st.rerun()
        else:
            answer_placeholder = st.empty()
            answer_text = ""
            citations: list[dict] = []
            retrieval_log_id = None  # Phase 3.2

            try:
                with logged_post(
                    f"{API_BASE_URL}/qa/stream",
                    json=payload,
                    headers=headers,
                    timeout=300,
                    stream=True,
                    operation_name="qa.stream",
                ) as resp:
                    if resp.status_code == 401:
                        success_expired()
                        del st.session_state["access_token"]
                        st.rerun()
                    resp.raise_for_status()
                    for raw_line in resp.iter_lines(decode_unicode=True):
                        if not raw_line:
                            continue
                        if not raw_line.startswith("data: "):
                            continue
                        line = raw_line[6:].strip()
                        if line == "[DONE]":
                            break
                        event = json.loads(line)
                        event_type = event.get("type")
                        if event_type == "answer":
                            answer_text += event.get("delta", "")
                            answer_placeholder.markdown(answer_text + "▌")
                        elif event_type == "citations":
                            citations = event.get("data", [])
                        elif event_type == "retrieval_log_id":  # Phase 3.2
                            retrieval_log_id = event.get("data")
                        elif event_type == "error":
                            st.error(event.get("message") or "流式问答失败")
                            break

                # 移除光标，显示最终回答
                # OPT-017: 无答案场景用醒目提示
                if answer_text.startswith("未检索到") or (not citations and "无法给出" in answer_text):
                    answer_placeholder.warning(answer_text)
                else:
                    answer_placeholder.markdown(answer_text)
                if citations:
                    with st.expander("📚 引用来源"):
                        for cite in citations:
                            st.caption(f"📄 文档 ID: {cite.get('document_id')} | 片段: {cite.get('chunk_index')}")
                # 添加到历史
                st.session_state["qa_chat_history"].append({
                    "role": "assistant",
                    "content": answer_text,
                    "citations": citations,
                    "retrieval_log_id": retrieval_log_id,  # Phase 3.2
                })
                st.session_state["_qa_input_counter"] = st.session_state.get("_qa_input_counter", 0) + 1  # 清空输入框
                st.rerun()

            except requests.exceptions.ConnectionError:
                err_network()
            except requests.exceptions.Timeout:
                err_timeout()
            except Exception as exc:  # noqa: BLE001
                err_business(f"请求失败：{exc}")

# 显示会话 ID
st.caption(f"会话 ID：`{conversation_id}`")
