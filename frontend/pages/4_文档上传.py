"""Document upload and list page."""

import os

import requests
import streamlit as st

from feedback import err_business, err_network, err_timeout, loading, success_expired, success_msg, warn_msg
from operation_log import logged_delete, logged_get, logged_post

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")


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
def fetch_knowledge_bases_cached(token: str) -> list[dict]:
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


@st.cache_data(ttl=8, show_spinner=False)
def fetch_documents_cached(token: str, knowledge_base_id: int) -> list[dict]:
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = logged_get(
            f"{API_BASE_URL}/knowledge-bases/{knowledge_base_id}/documents",
            headers=headers,
            timeout=20,
            operation_name="knowledge-bases.documents.list",
        )
        if resp.status_code == 401:
            return []
        data = resp.json()
        if data.get("code") != 0:
            return []
        return data.get("data", [])
    except Exception:
        return []


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
st.title("📄 文档管理")

if not check_auth():
    st.stop()

with st.spinner("加载知识库列表..."):
    token = _get_token()
    kb_items = fetch_knowledge_bases_cached(token)

if not kb_items:
    st.warning("📭 暂无知识库，请先到「知识库管理」页面创建")
    st.page_link("pages/3_知识库管理.py", label="前往创建知识库", icon="📚")
    st.stop()

kb_map = {f"📁 {item['name']}": item["id"] for item in kb_items}
selected_label = st.selectbox("📚 选择知识库", options=list(kb_map.keys()))
selected_kb_id = kb_map[selected_label]

# 获取当前知识库名称
current_kb_name = next((item["name"] for item in kb_items if item["id"] == selected_kb_id), "知识库")
st.subheader(f"当前知识库：{current_kb_name}")

st.divider()

# 上传区域（按 R4 规范）
st.subheader("📤 上传文档")
st.caption("支持 PDF, DOCX, TXT, MD, XLSX, PPTX, PNG, JPG（最大 50MB）")

files = st.file_uploader(
    "拖拽文件到此处或点击选择",
    accept_multiple_files=True,
    type=["txt", "md", "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "png", "jpg", "jpeg"],
    help="支持多选，最大 50MB/文件",
)
upload_submit = st.button("开始上传", type="primary", use_container_width=True)

if upload_submit:
    if not files:
        err_business("请至少选择一个文件")
    else:
        progress_bar = st.progress(0, text="准备上传...")
        try:
            if len(files) == 1:
                file_obj = files[0]
                progress_bar.progress(30, text=f"正在上传 {file_obj.name}...")
                resp = logged_post(
                    f"{API_BASE_URL}/knowledge-bases/{selected_kb_id}/documents",
                    files={"file": (file_obj.name, file_obj.getvalue(), file_obj.type or "application/octet-stream")},
                    headers=build_headers(),
                    timeout=120,
                    operation_name="documents.upload",
                )
                progress_bar.progress(100, text="上传完成")
                if resp.status_code == 401:
                    success_expired()
                    del st.session_state["access_token"]
                    st.rerun()
                data = resp.json()
                if data.get("code") == 0:
                    success_msg(f"上传成功：{file_obj.name}")
                    fetch_documents_cached.clear()
                    fetch_knowledge_bases_cached.clear()
                    st.rerun()
                else:
                    err_business(data.get("detail") or data.get("message") or "上传失败")
            else:
                progress_bar.progress(20, text=f"正在上传 {len(files)} 个文件...")
                multipart_files = [
                    ("files", (f.name, f.getvalue(), f.type or "application/octet-stream")) for f in files
                ]
                resp = logged_post(
                    f"{API_BASE_URL}/knowledge-bases/{selected_kb_id}/documents/batch",
                    files=multipart_files,
                    headers=build_headers(),
                    timeout=300,
                    operation_name="documents.batch_upload",
                )
                progress_bar.progress(100, text="上传完成")
                if resp.status_code == 401:
                    success_expired()
                    del st.session_state["access_token"]
                    st.rerun()
                data = resp.json()
                if data.get("code") == 0:
                    success_count = data["data"]["success_count"]
                    failed_count = data["data"]["failed_count"]
                    if failed_count == 0:
                        success_msg(f"批量上传完成：全部 {success_count} 个文件成功")
                    else:
                        warn_msg(f"批量上传完成：成功 {success_count}，失败 {failed_count}")
                    if data["data"]["failed_items"]:
                        with st.expander("查看失败详情"):
                            st.json(data["data"]["failed_items"])
                    fetch_documents_cached.clear()
                    fetch_knowledge_bases_cached.clear()
                    st.rerun()
                else:
                    err_business(data.get("detail") or data.get("message") or "批量上传失败")
        except requests.exceptions.ConnectionError:
            err_network()
        except requests.exceptions.Timeout:
            err_timeout()
        except Exception as exc:  # noqa: BLE001
            err_business(f"请求失败：{exc}")

st.divider()
st.subheader("📋 文档列表")

col_search, col_filter, col_refresh = st.columns([2, 1, 1])
with col_search:
    search_filename = st.text_input("🔍 搜索文件名", placeholder="输入文件名...", label_visibility="collapsed")
with col_filter:
    status_filter = st.selectbox("状态筛选", ["全部", "处理中", "成功", "失败"], label_visibility="collapsed")
with col_refresh:
    if st.button("🔄 刷新列表", use_container_width=True):
        fetch_documents_cached.clear()
        st.rerun()

with loading("加载文档列表..."):
    try:
        docs = fetch_documents_cached(_get_token(), selected_kb_id)
        if not docs and not _get_token():
            success_expired()
            st.rerun()
        else:
            # 搜索和筛选
            if search_filename:
                docs = [d for d in docs if search_filename.lower() in d["filename"].lower()]
            if status_filter == "处理中":
                docs = [d for d in docs if d["status"] in ("uploaded", "parsing", "vectorizing")]
            elif status_filter == "成功":
                docs = [d for d in docs if d["status"] in ("parsed", "vectorized")]
            elif status_filter == "失败":
                docs = [d for d in docs if "failed" in d["status"]]
            
            st.caption(f"共 {len(docs)} 个文档")
            if not docs:
                st.info("📭 当前知识库暂无文档，请上传")
            else:
                # 状态图标映射（按 R4 规范）
                status_icons = {
                    "uploaded": "🔄",
                    "parsing": "🔄",
                    "parsed": "📝",
                    "vectorizing": "🔄",
                    "vectorized": "✅",
                    "parse_failed": "❌",
                    "vectorize_failed": "❌",
                    "parser_not_implemented": "⚠️",
                }
                st.dataframe(
                    [
                        {
                            "ID": doc["id"],
                            "文件名": doc["filename"],
                            "状态": f"{status_icons.get(doc['status'], '❓')} {doc['status']}",
                            "大小": f"{doc['file_size'] / 1024:.1f} KB" if doc["file_size"] else "-",
                            "更新时间": doc["updated_at"][:16] if doc.get("updated_at") else "-",
                        }
                        for doc in docs
                    ],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "状态": st.column_config.TextColumn("状态", help="✅ 成功, 🔄 处理中, ❌ 失败"),
                    },
                )

                # 文档操作区
                st.subheader("文档操作")
                col_select, col_action = st.columns([2, 1])
                with col_select:
                    doc_options = {f"{d['filename']} (ID={d['id']}, v{d.get('version', 1)})": d["id"] for d in docs}
                    selected_doc_label = st.selectbox("选择文档", options=list(doc_options.keys()), key="doc_select")
                    selected_doc_id = doc_options[selected_doc_label]

                with col_action:
                    st.write("")  # 占位对齐
                    col_reparse, col_dl, col_del = st.columns(3)
                    with col_reparse:
                        if st.button("🔄 重新解析", use_container_width=True, help="重新解析并向量化该文档"):
                            try:
                                with loading("正在重新解析..."):
                                    reparse_resp = logged_post(
                                        f"{API_BASE_URL}/documents/{selected_doc_id}/reparse",
                                        headers=build_headers(),
                                        timeout=180,
                                        operation_name="documents.reparse",
                                    )
                                    reparse_data = reparse_resp.json()
                                    if reparse_data.get("code") == 0:
                                        success_msg("重新解析完成")
                                        fetch_documents_cached.clear()
                                        st.rerun()
                                    else:
                                        err_business(reparse_data.get("detail") or reparse_data.get("message") or "重新解析失败")
                            except Exception as e:
                                err_business(f"重新解析失败：{e}")
                    with col_dl:
                        if st.button("📥 下载", use_container_width=True):
                            try:
                                dl_resp = logged_get(
                                    f"{API_BASE_URL}/documents/{selected_doc_id}/download",
                                    headers=build_headers(),
                                    timeout=60,
                                    operation_name="documents.download",
                                )
                                if dl_resp.status_code == 200:
                                    # 获取文件名
                                    selected_doc = next((d for d in docs if d["id"] == selected_doc_id), None)
                                    filename = selected_doc["filename"] if selected_doc else "download"
                                    st.download_button(
                                        label="💾 保存文件",
                                        data=dl_resp.content,
                                        file_name=filename,
                                        mime="application/octet-stream",
                                        key="save_file_btn",
                                    )
                                else:
                                    err_business(f"下载失败：{dl_resp.status_code}")
                            except Exception as e:
                                err_business(f"下载失败：{e}")
                    with col_del:
                        if st.button("🗑️ 删除", use_container_width=True, type="secondary"):
                            try:
                                del_resp = logged_delete(
                                    f"{API_BASE_URL}/documents/{selected_doc_id}",
                                    headers=build_headers(),
                                    timeout=30,
                                    operation_name="documents.delete",
                                )
                                if del_resp.status_code == 200:
                                    success_msg("删除成功")
                                    fetch_documents_cached.clear()
                                    st.rerun()
                                else:
                                    err_business(f"删除失败：{del_resp.status_code}")
                            except Exception as e:
                                err_business(f"删除失败：{e}")

                # ========== 版本管理区 ==========
                st.divider()
                st.subheader("📜 版本管理")
                
                # 获取选中文档的版本历史
                try:
                    versions_resp = logged_get(
                        f"{API_BASE_URL}/documents/{selected_doc_id}/versions",
                        headers=build_headers(),
                        timeout=15,
                        operation_name="documents.versions.list",
                    )
                    versions_data = versions_resp.json()
                    if versions_data.get("code") == 0:
                        versions = versions_data.get("data", [])
                        if len(versions) <= 1:
                            st.info("📄 该文档仅有当前版本，暂无历史版本")
                        else:
                            st.caption(f"共 {len(versions)} 个版本")
                            
                            # 版本列表
                            for v in versions:
                                v_id = v["id"]
                                v_num = v.get("version", 1)
                                v_is_current = v.get("is_current", False)
                                v_created = v.get("created_at", "")[:16] if v.get("created_at") else "-"
                                v_status = v.get("status", "unknown")
                                
                                with st.container():
                                    col_info, col_btn = st.columns([3, 1])
                                    with col_info:
                                        current_badge = "🟢 当前版本" if v_is_current else ""
                                        st.markdown(f"**v{v_num}** {current_badge}")
                                        st.caption(f"ID: {v_id} | 状态: {v_status} | 创建: {v_created}")
                                    with col_btn:
                                        if not v_is_current:
                                            if st.button(f"🔀 切换到 v{v_num}", key=f"activate_{v_id}", use_container_width=True):
                                                try:
                                                    with loading(f"正在切换到版本 {v_num}..."):
                                                        activate_resp = logged_post(
                                                            f"{API_BASE_URL}/documents/{v_id}/activate",
                                                            headers=build_headers(),
                                                            timeout=120,
                                                            operation_name="documents.version.activate",
                                                        )
                                                        activate_data = activate_resp.json()
                                                        if activate_data.get("code") == 0:
                                                            success_msg(f"已切换到版本 {v_num}，向量库已同步")
                                                            fetch_documents_cached.clear()
                                                            st.rerun()
                                                        else:
                                                            err_business(activate_data.get("detail") or activate_data.get("message") or "版本切换失败")
                                                except Exception as e:
                                                    err_business(f"版本切换失败：{e}")
                                        else:
                                            st.button("✓ 当前", key=f"current_{v_id}", disabled=True, use_container_width=True)
                                    st.divider()
                    else:
                        err_business(versions_data.get("detail") or versions_data.get("message") or "获取版本历史失败")
                except Exception as e:
                    err_business(f"获取版本历史失败：{e}")
    except requests.exceptions.ConnectionError:
        err_network()
    except Exception as exc:  # noqa: BLE001
        err_business(f"加载失败：{exc}")
