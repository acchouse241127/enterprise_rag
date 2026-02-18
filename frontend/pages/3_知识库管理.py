"""Knowledge base management page."""

import os

import requests
import streamlit as st

from feedback import err_business, err_network, loading, success_expired, success_msg
from operation_log import logged_delete, logged_get, logged_post

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# 状态图标映射
STATUS_ICONS = {
    "pending": "⏳",
    "parsing": "🔄",
    "parsed": "📝",
    "vectorizing": "🔢",
    "vectorized": "✅",
    "parse_failed": "❌",
    "vectorize_failed": "⚠️",
}


def build_headers() -> dict:
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _get_token() -> str:
    return st.session_state.get("access_token", "")


def format_file_size(size_bytes: int | None) -> str:
    """Format file size to human readable string."""
    if not size_bytes:
        return "-"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


@st.cache_data(ttl=8, show_spinner=False)
def _fetch_kb_documents_cached(kb_id: int, token: str) -> list[dict]:
    """Fetch documents for a knowledge base with short cache."""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/knowledge-bases/{kb_id}/documents",
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=12,
            operation_name="knowledge-bases.documents.list",
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", [])
    except Exception:
        pass
    return []


def fetch_kb_documents(kb_id: int) -> list[dict]:
    return _fetch_kb_documents_cached(kb_id, _get_token())


@st.cache_data(ttl=8, show_spinner=False)
def fetch_knowledge_bases_cached(
    token: str, sort_by: str = "created_at", order: str = "desc"
) -> list[dict]:
    """OPT-026: 支持 sort_by=created_at|name, order=asc|desc."""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/knowledge-bases",
            params={"sort_by": sort_by, "order": order},
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=12,
            operation_name="knowledge-bases.list",
        )
        if resp.status_code == 401:
            return []
        data = resp.json()
        if data.get("code") != 0:
            return []
        return data.get("data", [])
    except Exception:
        return []


def download_document(doc_id: int, filename: str):
    """Download a document."""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/documents/{doc_id}/download",
            headers=build_headers(),
            timeout=60,
            operation_name="documents.download",
        )
        if resp.status_code == 200:
            return resp.content, filename
    except Exception:
        pass
    return None, None


def preview_document(doc_id: int) -> str | None:
    """Get document preview (parsed content)."""
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


def check_auth() -> bool:
    """Check if user is authenticated."""
    if not st.session_state.get("access_token"):
        st.warning("⚠️ 请先登录后再使用此功能")
        st.page_link("pages/1_登录.py", label="前往登录", icon="🔐")
        return False
    return True


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
    st.caption("💬 对话 | 📚 知识库 | 📄 文档")

# ========== 主内容区 ==========
st.title("📚 知识库管理")

# 模块使用说明（精华）
with st.container(border=True):
    st.markdown("**📌 使用说明**")
    st.markdown("知识库是文档的容器，可按主题或项目划分。创建后可在「文档上传」中上传文档，在「RAG 问答」中选择知识库提问。")
    st.caption("💡 提示：点击「管理文档」可查看、重新解析、预览、下载或删除该知识库下的文档。")

if not check_auth():
    st.stop()

st.markdown("---")

# 新建知识库表单（按 R4 规范使用 st.form）
with st.form("create_kb_form"):
    st.subheader("➕ 新建知识库")
    kb_name = st.text_input("知识库名称 *", placeholder="例如：公司制度文档、产品手册")
    kb_desc = st.text_area("描述（可选）", height=70, placeholder="简要描述知识库的用途或主题")
    create_submit = st.form_submit_button("创建", type="primary", use_container_width=True)

if create_submit:
    if not kb_name.strip():
        err_business("知识库名称不能为空")
    else:
        with loading("正在创建知识库..."):
            try:
                resp = logged_post(
                    f"{API_BASE_URL}/knowledge-bases",
                    json={"name": kb_name.strip(), "description": kb_desc.strip() or None},
                    headers=build_headers(),
                    timeout=15,
                    operation_name="knowledge-bases.create",
                )
                if resp.status_code == 401:
                    success_expired()
                    del st.session_state["access_token"]
                    st.rerun()
                data = resp.json()
                if data.get("code") == 0:
                    success_msg("知识库创建成功")
                    fetch_knowledge_bases_cached.clear()
                    st.rerun()
                else:
                    err_business(data.get("detail") or data.get("message") or "创建失败")
            except requests.exceptions.ConnectionError:
                err_network()
            except Exception as exc:  # noqa: BLE001
                err_business(f"请求失败：{exc}")

st.markdown("---")
# 知识库列表：标题与工具栏同一行，图标简洁单一，避免堆叠杂乱
row_title, row_tool = st.columns([1, 3])
with row_title:
    st.markdown("### 📚 知识库列表")
with row_tool:
    col_search, col_sort, col_refresh = st.columns([2, 1, 1])
    with col_search:
        search_query = st.text_input("搜索", placeholder="输入名称...", label_visibility="collapsed", key="kb_search_input")
    with col_sort:
        sort_by = st.selectbox(
            "排序",
            options=["created_at", "name"],
            format_func=lambda x: "创建时间" if x == "created_at" else "名称",
            key="kb_sort_by",
        )
        order = st.selectbox(
            "顺序",
            options=["desc", "asc"],
            format_func=lambda x: "降序" if x == "desc" else "升序",
            key="kb_order",
        )
    with col_refresh:
        st.write("")
        refresh = st.button("🔄 刷新", use_container_width=True)
if refresh:
    fetch_knowledge_bases_cached.clear()
    _fetch_kb_documents_cached.clear()

with loading("加载知识库列表..."):
    try:
        items = fetch_knowledge_bases_cached(
            _get_token(),
            sort_by=st.session_state.get("kb_sort_by", "created_at"),
            order=st.session_state.get("kb_order", "desc"),
        )
        
        # 搜索过滤
        if search_query:
            items = [item for item in items if search_query.lower() in item["name"].lower()]

        st.caption(f"共 {len(items)} 个知识库")

        if not items:
            st.info("📭 暂无知识库，请在上方创建")
        else:
            # 使用卡片式布局（按 R4 规范，3 列）
            cols = st.columns(3)
            for idx, item in enumerate(items):
                doc_count = item.get("document_count", 0)
                kb_id = item["id"]
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.markdown(f"### 📁 {item['name']}")
                        st.caption(f"📄 文档数: {doc_count}  |  📅 创建: {item['created_at'][:10]}")
                        if item.get("description"):
                            st.caption(item["description"][:50] + ("..." if len(item.get("description", "")) > 50 else ""))
                        
                        col_manage, col_del = st.columns(2)
                        with col_manage:
                            if st.button("📂 管理文档", key=f"btn_manage_{kb_id}", use_container_width=True):
                                st.session_state["selected_kb_for_docs"] = kb_id
                        with col_del:
                            if st.button("🗑️ 删除", key=f"del_kb_{kb_id}", type="secondary", use_container_width=True):
                                if doc_count > 0:
                                    st.warning(f"⚠️ 该知识库包含 {doc_count} 个文档")
                                with loading("正在删除..."):
                                    try:
                                        del_resp = logged_delete(
                                            f"{API_BASE_URL}/knowledge-bases/{kb_id}",
                                            headers=build_headers(),
                                            timeout=30,
                                            operation_name="knowledge-bases.delete",
                                        )
                                        del_data = del_resp.json()
                                        if del_data.get("code") == 0:
                                            success_msg(f"已删除：{item['name']}")
                                            fetch_knowledge_bases_cached.clear()
                                            _fetch_kb_documents_cached.clear()
                                            st.rerun()
                                        else:
                                            # OPT-026: 500 时后端可能返回 {"detail": "..."}
                                            err_business(
                                                del_data.get("detail")
                                                or del_data.get("message")
                                                or "删除失败"
                                            )
                                    except Exception as exc:  # noqa: BLE001
                                        err_business(f"请求失败：{exc}")

            # 文档列表展开区域（在卡片外部显示）
            selected_kb_for_docs = st.session_state.get("selected_kb_for_docs")
            if selected_kb_for_docs:
                selected_item = next((item for item in items if item["id"] == selected_kb_for_docs), None)
                if selected_item:
                    doc_count = selected_item.get("document_count", 0)
                    kb_id = selected_item["id"]
                    st.divider()
                    with st.expander(f"📄 {selected_item['name']} 的文档列表 ({doc_count} 个文件)", expanded=True):
                            documents = fetch_kb_documents(kb_id)
                            if not documents:
                                st.info("无法加载文档列表")
                            else:
                                for doc in documents:
                                    doc_id = doc["id"]
                                    filename = doc["filename"]
                                    status = doc.get("status", "unknown")
                                    status_icon = STATUS_ICONS.get(status, "❓")
                                    file_size = format_file_size(doc.get("file_size"))

                                    with st.container(border=True):
                                        doc_col1, doc_col2, doc_col3, doc_col4, doc_col5 = st.columns([3, 1, 1, 1, 1])
                                        with doc_col1:
                                            st.markdown(f"**📄 {filename}**")
                                            st.caption(f"大小: {file_size} | 状态: {status_icon} {status}")
                                            if doc.get("parser_message"):
                                                st.caption(f"解析信息: {doc['parser_message']}")

                                        with doc_col2:
                                            if st.button("🔄 重新解析", key=f"reparse_{kb_id}_{doc_id}", use_container_width=True):
                                                try:
                                                    r = logged_post(
                                                        f"{API_BASE_URL}/documents/{doc_id}/reparse",
                                                        headers=build_headers(),
                                                        timeout=180,
                                                        operation_name="documents.reparse",
                                                    )
                                                    d = r.json()
                                                    if d.get("code") == 0:
                                                        success_msg("重新解析完成")
                                                        _fetch_kb_documents_cached.clear()
                                                        st.rerun()
                                                    else:
                                                        err_business(d.get("detail") or d.get("message") or "重新解析失败")
                                                except Exception as e:
                                                    err_business(str(e))

                                        with doc_col3:
                                            if st.button("👁️ 预览", key=f"preview_{kb_id}_{doc_id}", use_container_width=True):
                                                content = preview_document(doc_id)
                                                if content:
                                                    st.session_state[f"preview_content_{doc_id}"] = content
                                                else:
                                                    st.warning("无法获取预览内容")

                                        with doc_col4:
                                            if st.button("📥 下载", key=f"download_{kb_id}_{doc_id}", use_container_width=True):
                                                file_content, file_name = download_document(doc_id, filename)
                                                if file_content:
                                                    st.download_button(
                                                        label="💾 保存",
                                                        data=file_content,
                                                        file_name=file_name,
                                                        mime="application/octet-stream",
                                                        key=f"save_{kb_id}_{doc_id}",
                                                    )
                                                else:
                                                    err_business("下载失败")

                                        with doc_col5:
                                            if st.button("🗑️ 删除", key=f"del_doc_{kb_id}_{doc_id}", use_container_width=True, type="secondary"):
                                                try:
                                                    del_resp = logged_delete(
                                                        f"{API_BASE_URL}/documents/{doc_id}",
                                                        headers=build_headers(),
                                                        timeout=30,
                                                        operation_name="documents.delete",
                                                    )
                                                    if del_resp.status_code == 200:
                                                        data = del_resp.json()
                                                        if data.get("code") == 0:
                                                            success_msg("文档已删除")
                                                            _fetch_kb_documents_cached.clear()
                                                            fetch_knowledge_bases_cached.clear()
                                                            st.rerun()
                                                        else:
                                                            err_business(data.get("detail") or data.get("message") or "删除失败")
                                                    else:
                                                        err_business("删除失败")
                                                except Exception as e:
                                                    err_business(str(e))

                                        # 显示预览内容
                                        preview_key = f"preview_content_{doc_id}"
                                        if preview_key in st.session_state:
                                            st.divider()
                                            st.markdown("**📖 文档内容预览：**")
                                            preview_text = st.session_state[preview_key]
                                            # 限制预览长度
                                            if len(preview_text) > 2000:
                                                preview_text = preview_text[:2000] + "\n\n... (内容已截断，共 {} 字符)".format(len(st.session_state[preview_key]))
                                            st.text_area(
                                                "内容",
                                                value=preview_text,
                                                height=300,
                                                disabled=True,
                                                key=f"preview_area_{kb_id}_{doc_id}",
                                                label_visibility="collapsed",
                                            )
                                            if st.button("关闭预览", key=f"close_preview_{kb_id}_{doc_id}"):
                                                del st.session_state[preview_key]
                                                st.rerun()
    except requests.exceptions.ConnectionError:
        err_network()
    except Exception as exc:  # noqa: BLE001
        err_business(f"加载失败：{exc}")

