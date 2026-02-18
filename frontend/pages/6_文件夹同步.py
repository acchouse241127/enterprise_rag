"""Folder sync management page.

Phase 3.2: 文件夹同步配置
Author: C2
Date: 2026-02-13
"""

import os

import streamlit as st

from feedback import err_business, loading, success_msg
from operation_log import logged_delete, logged_get, logged_post

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# 同步状态图标
SYNC_STATUS_ICONS = {
    "idle": "⏸️",
    "running": "🔄",
    "success": "✅",
    "failed": "❌",
}


def build_headers() -> dict:
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def check_auth() -> bool:
    """Check if user is authenticated."""
    if not st.session_state.get("access_token"):
        st.warning("⚠️ 请先登录后再使用此功能")
        st.page_link("pages/1_登录.py", label="前往登录", icon="🔐")
        return False
    return True


@st.cache_data(ttl=8, show_spinner=False)
def fetch_knowledge_bases(token: str) -> list:
    """Fetch knowledge bases."""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/knowledge-bases",
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=12,
            operation_name="knowledge-bases.list",
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", [])
    except Exception:
        pass
    return []


def fetch_sync_config(kb_id: int) -> dict | None:
    """Fetch folder sync config for a knowledge base."""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/knowledge-bases/{kb_id}/folder-sync",
            headers=build_headers(),
            timeout=10,
            operation_name="folder-sync.config.get",
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data")
    except Exception:
        pass
    return None


def fetch_sync_logs(kb_id: int, limit: int = 10) -> list:
    """Fetch sync logs for a knowledge base."""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/knowledge-bases/{kb_id}/folder-sync/logs",
            params={"limit": limit},
            headers=build_headers(),
            timeout=10,
            operation_name="folder-sync.logs.list",
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", [])
    except Exception:
        pass
    return []


# ========== 侧边栏 ==========
with st.sidebar:
    st.title("🏠 Enterprise RAG")
    username = st.session_state.get("username", "用户")
    st.markdown(f"👤 **{username}**")
    if st.button("🚪 登出", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()
    st.caption("📁 文件夹同步")

# ========== 主内容区 ==========
st.title("📁 文件夹同步")

if not check_auth():
    st.stop()

token = st.session_state.get("access_token", "")

# ========== 选择知识库 ==========
st.subheader("🎯 选择知识库")

kbs = fetch_knowledge_bases(token)
if not kbs:
    st.warning("⚠️ 暂无知识库，请先创建知识库")
    st.page_link("pages/3_知识库管理.py", label="前往创建", icon="📚")
    st.stop()

kb_options = {kb["name"]: kb["id"] for kb in kbs}
selected_kb_name = st.selectbox("知识库", options=list(kb_options.keys()))
selected_kb_id = kb_options[selected_kb_name]

st.divider()

# ========== 当前配置 ==========
st.subheader("⚙️ 同步配置")

config = fetch_sync_config(selected_kb_id)

if config:
    # 显示当前配置
    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**📂 同步目录:** `{config['directory_path']}`")
            st.caption(f"文件模式: {config['file_patterns']}")
            st.caption(f"同步间隔: {config['sync_interval_minutes']} 分钟")
            enabled_badge = "🟢 已启用" if config['enabled'] else "🔴 已禁用"
            st.caption(f"状态: {enabled_badge}")

        with col2:
            status = config.get("last_sync_status", "idle")
            status_icon = SYNC_STATUS_ICONS.get(status, "❓")
            st.markdown(f"**最近同步: {status_icon} {status}**")
            if config.get("last_sync_at"):
                st.caption(f"时间: {config['last_sync_at'][:16]}")
            st.caption(f"新增: {config.get('last_sync_files_added', 0)} | "
                      f"更新: {config.get('last_sync_files_updated', 0)} | "
                      f"删除: {config.get('last_sync_files_deleted', 0)}")
            if config.get("last_sync_message"):
                st.caption(f"消息: {config['last_sync_message'][:50]}")

    # 操作按钮
    col_sync, col_edit, col_delete = st.columns(3)

    with col_sync:
        if st.button("🔄 立即同步", use_container_width=True, type="primary"):
            with loading("正在同步文件夹..."):
                try:
                    resp = logged_post(
                        f"{API_BASE_URL}/knowledge-bases/{selected_kb_id}/folder-sync/trigger",
                        headers=build_headers(),
                        timeout=300,
                        operation_name="folder-sync.trigger",
                    )
                    data = resp.json()
                    if data.get("code") == 0:
                        result = data.get("data", {})
                        success_msg(
                            f"同步完成！扫描 {result.get('files_scanned', 0)} 文件，"
                            f"新增 {result.get('files_added', 0)}，"
                            f"更新 {result.get('files_updated', 0)}，"
                            f"耗时 {result.get('duration_seconds', 0):.1f} 秒"
                        )
                        st.rerun()
                    else:
                        err_business(data.get("detail") or data.get("message") or "同步失败")
                except Exception as e:
                    err_business(f"同步失败: {e}")

    with col_edit:
        if st.button("✏️ 修改配置", use_container_width=True):
            st.session_state["edit_sync_config"] = True

    with col_delete:
        if st.button("🗑️ 删除配置", use_container_width=True, type="secondary"):
            try:
                resp = logged_delete(
                    f"{API_BASE_URL}/knowledge-bases/{selected_kb_id}/folder-sync",
                    headers=build_headers(),
                    timeout=10,
                    operation_name="folder-sync.config.delete",
                )
                if resp.json().get("code") == 0:
                    success_msg("配置已删除")
                    st.rerun()
                else:
                    err_business("删除失败")
            except Exception as e:
                err_business(str(e))

    # 编辑表单
    if st.session_state.get("edit_sync_config"):
        st.divider()
        st.markdown("**✏️ 修改同步配置**")
        st.caption("💡 路径为**服务端路径**；Docker 部署时为**容器内**路径。")
        if "edit_sync_dir" not in st.session_state:
            st.session_state["edit_sync_dir"] = config["directory_path"]
        st.markdown("**同步目录**")
        preset_edit = [
            ("/data", "📂 /data"),
            ("/app/data", "📂 /app/data"),
            ("/home/user/docs", "📂 /home/user/docs"),
            ("C:\\Data", "📂 C:\\Data"),
            ("C:\\Documents", "📂 C:\\Documents"),
        ]
        cols_edit = st.columns(len(preset_edit))
        for i, (path_val, label) in enumerate(preset_edit):
            with cols_edit[i]:
                if st.button(label, key=f"preset_edit_{i}", use_container_width=True):
                    st.session_state["edit_sync_dir"] = path_val
                    st.rerun()
        with st.form("edit_sync_form"):
            new_dir = st.text_input(
                "同步目录",
                value=st.session_state.get("edit_sync_dir", config["directory_path"]),
                key="edit_sync_dir",
            )
            new_interval = st.number_input(
                "同步间隔（分钟）",
                min_value=5,
                max_value=1440,
                value=config["sync_interval_minutes"],
            )
            new_patterns = st.text_input("文件模式", value=config["file_patterns"])
            new_enabled = st.checkbox("启用同步", value=config["enabled"])

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                if st.form_submit_button("保存", type="primary", use_container_width=True):
                    try:
                        resp = logged_post(
                            f"{API_BASE_URL}/knowledge-bases/{selected_kb_id}/folder-sync",
                            json={
                                "directory_path": new_dir,
                                "sync_interval_minutes": new_interval,
                                "file_patterns": new_patterns,
                                "enabled": new_enabled,
                            },
                            headers=build_headers(),
                            timeout=15,
                            operation_name="folder-sync.config.update",
                        )
                        if resp.json().get("code") == 0:
                            success_msg("配置已更新")
                            st.session_state["edit_sync_config"] = False
                            st.rerun()
                        else:
                            err_business(resp.json().get("detail") or "更新失败")
                    except Exception as e:
                        err_business(str(e))
            with col_cancel:
                if st.form_submit_button("取消", use_container_width=True):
                    st.session_state["edit_sync_config"] = False
                    st.rerun()

else:
    # 无配置，显示创建表单
    st.info("📭 尚未配置文件夹同步")

    st.markdown("**➕ 创建同步配置**")
    st.caption("💡 路径为**服务端路径**；Docker 部署时为**容器内**路径。")
    # Browse / 选择文件夹：多选该文件夹内文件后，将文件夹路径填入下方同步目录
    browse_files = st.file_uploader(
        "Browse / 选择文件夹",
        type=["txt", "md", "pdf", "doc", "docx", "xlsx", "pptx", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="点击后选择需要同步的文件夹内的文件（可多选同一文件夹下文件），然后将该文件夹的完整路径填入下方「同步目录」。",
        key="sync_browse_create",
    )
    if browse_files:
        st.caption(f"已选 **{len(browse_files)}** 个文件（如：{browse_files[0].name} 等）— 请将包含这些文件的**文件夹路径**填入下方「同步目录」。")

    # 同步目录：支持一键填入常用路径（“选择文件夹”快捷方式）
    if "create_sync_dir" not in st.session_state:
        st.session_state["create_sync_dir"] = ""
    st.markdown("**同步目录 \***")
    preset_paths = [
        ("/data", "📂 /data"),
        ("/app/data", "📂 /app/data"),
        ("/home/user/docs", "📂 /home/user/docs"),
        ("C:\\Data", "📂 C:\\Data"),
        ("C:\\Documents", "📂 C:\\Documents"),
    ]
    preset_cols = st.columns(len(preset_paths))
    for i, (path_val, label) in enumerate(preset_paths):
        with preset_cols[i]:
            if st.button(label, key=f"preset_create_{i}", use_container_width=True):
                st.session_state["create_sync_dir"] = path_val
                st.rerun()
    with st.form("create_sync_form"):
        dir_path = st.text_input(
            "同步目录",
            value=st.session_state.get("create_sync_dir", ""),
            placeholder="例如: /data/docs 或 C:\\Documents\\MyKnowledge",
            key="create_sync_dir",
        )
        interval = st.number_input(
            "同步间隔（分钟）",
            min_value=5,
            max_value=1440,
            value=30,
            help="定时扫描同步的间隔时间",
        )
        patterns = st.text_input(
            "文件模式",
            value="*.txt,*.md,*.pdf,*.docx,*.xlsx,*.pptx,*.png,*.jpg,*.jpeg",
            help="逗号分隔的文件匹配模式（与文档管理上传格式一致，含图片 png/jpg）",
        )
        enabled = st.checkbox("立即启用", value=True)

        if st.form_submit_button("创建配置", type="primary", use_container_width=True):
            if not dir_path.strip():
                err_business("请输入同步目录")
            else:
                try:
                    resp = logged_post(
                        f"{API_BASE_URL}/knowledge-bases/{selected_kb_id}/folder-sync",
                        json={
                            "directory_path": dir_path.strip(),
                            "sync_interval_minutes": interval,
                            "file_patterns": patterns,
                            "enabled": enabled,
                        },
                        headers=build_headers(),
                        timeout=15,
                        operation_name="folder-sync.config.create",
                    )
                    data = resp.json()
                    if data.get("code") == 0:
                        success_msg("同步配置创建成功")
                        st.rerun()
                    else:
                        err_business(data.get("detail") or data.get("message") or "创建失败")
                except Exception as e:
                    err_business(f"创建失败: {e}")

st.divider()

# ========== 同步日志 ==========
st.subheader("📜 同步日志")

logs = fetch_sync_logs(selected_kb_id)

if logs:
    for log in logs:
        status = log.get("status", "unknown")
        status_icon = SYNC_STATUS_ICONS.get(status, "❓")
        triggered = "🖱️ 手动" if log.get("triggered_by") == "manual" else "⏰ 定时"
        created_at = log.get("created_at", "")[:16]
        duration = log.get("duration_seconds", 0)

        with st.container(border=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**{status_icon} {status}** - {triggered}")
                st.caption(f"时间: {created_at} | 耗时: {duration:.1f}s")
                if log.get("message"):
                    st.caption(f"消息: {log['message'][:80]}")

            with col2:
                st.caption(
                    f"扫描: {log.get('files_scanned', 0)} | "
                    f"新增: {log.get('files_added', 0)} | "
                    f"更新: {log.get('files_updated', 0)}"
                )
                st.caption(
                    f"删除: {log.get('files_deleted', 0)} | "
                    f"失败: {log.get('files_failed', 0)}"
                )
else:
    st.info("📭 暂无同步日志")
