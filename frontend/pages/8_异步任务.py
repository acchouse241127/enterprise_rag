"""
Async task monitoring page.

Phase 3.3: 异步任务队列
Author: C2
Date: 2026-02-14
"""

import os
from datetime import datetime

import streamlit as st

from feedback import err_business, err_network, success_msg
from operation_log import logged_get, logged_post

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")


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


def fetch_tasks(task_type: str | None = None, status: str | None = None) -> list[dict]:
    """Fetch async tasks."""
    try:
        params = {}
        if task_type:
            params["task_type"] = task_type
        if status:
            params["status"] = status
        resp = logged_get(
            f"{API_BASE_URL}/tasks",
            headers=build_headers(),
            params=params,
            timeout=10,
            operation_name="tasks.list",
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("tasks", [])
        return []
    except Exception:
        return []


def get_status_badge(status: str) -> str:
    """Get status badge emoji."""
    badges = {
        "pending": "⏳ 待处理",
        "running": "🔄 执行中",
        "success": "✅ 成功",
        "failed": "❌ 失败",
        "cancelled": "🚫 已取消",
    }
    return badges.get(status, status)


def get_task_type_label(task_type: str) -> str:
    """Get task type label."""
    labels = {
        "document_parse": "📄 文档解析",
        "document_vectorize": "🔢 文档向量化",
        "folder_sync": "📁 文件夹同步",
        "export_conversation": "💬 对话导出",
    }
    return labels.get(task_type, task_type)


def main():
    st.set_page_config(page_title="异步任务", page_icon="⚙️", layout="wide")
    st.title("⚙️ 异步任务监控")
    st.caption("查看和管理后台异步任务")

    if not check_auth():
        return

    # Sidebar filters
    with st.sidebar:
        st.subheader("筛选条件")

        task_type_options = {
            "全部": None,
            "文档解析": "document_parse",
            "文档向量化": "document_vectorize",
            "文件夹同步": "folder_sync",
            "对话导出": "export_conversation",
        }
        selected_type_label = st.selectbox("任务类型", list(task_type_options.keys()))
        selected_type = task_type_options[selected_type_label]

        status_options = {
            "全部": None,
            "待处理": "pending",
            "执行中": "running",
            "成功": "success",
            "失败": "failed",
            "已取消": "cancelled",
        }
        selected_status_label = st.selectbox("状态", list(status_options.keys()))
        selected_status = status_options[selected_status_label]

        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()

    # Auto-refresh toggle
    auto_refresh = st.checkbox("自动刷新（每 5 秒）", value=False)
    if auto_refresh:
        import time
        time.sleep(5)
        st.rerun()

    # Fetch tasks
    tasks = fetch_tasks(selected_type, selected_status)

    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    pending_count = len([t for t in tasks if t.get("status") == "pending"])
    running_count = len([t for t in tasks if t.get("status") == "running"])
    success_count = len([t for t in tasks if t.get("status") == "success"])
    failed_count = len([t for t in tasks if t.get("status") == "failed"])

    with col1:
        st.metric("总任务数", len(tasks))
    with col2:
        st.metric("待处理", pending_count)
    with col3:
        st.metric("执行中", running_count)
    with col4:
        st.metric("成功", success_count)
    with col5:
        st.metric("失败", failed_count)

    st.divider()

    if not tasks:
        st.info("📭 暂无任务记录")
        return

    # Display tasks
    st.subheader("任务列表")

    for task in tasks:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                st.markdown(f"**{get_task_type_label(task.get('task_type', ''))}**")
                st.caption(f"任务 ID: {task.get('id')}")
                if task.get("entity_type") and task.get("entity_id"):
                    st.caption(f"关联: {task['entity_type']} #{task['entity_id']}")

            with col2:
                status = task.get("status", "")
                st.markdown(get_status_badge(status))

                # Progress bar for running tasks
                progress = task.get("progress", 0)
                if status == "running":
                    st.progress(progress / 100, text=f"{progress:.1f}%")
                elif status == "success":
                    st.progress(1.0, text="100%")

                # Message
                message = task.get("message")
                if message:
                    st.caption(message)

                # Error message for failed tasks
                if status == "failed" and task.get("error_message"):
                    st.error(task["error_message"][:100])

            with col3:
                # Timing info
                created_at = task.get("created_at", "")
                if created_at:
                    st.caption(f"创建: {created_at[:19].replace('T', ' ')}")

                started_at = task.get("started_at")
                if started_at:
                    st.caption(f"开始: {started_at[:19].replace('T', ' ')}")

                completed_at = task.get("completed_at")
                if completed_at:
                    st.caption(f"完成: {completed_at[:19].replace('T', ' ')}")

                # Cancel button for pending/running tasks
                # OPT-022: 增强取消功能，支持 pending 状态取消，并明确展示取消后状态
                if status in ("pending", "running"):
                    cancel_label = "🚫 取消" if status == "pending" else "⏹️ 停止"
                    if st.button(cancel_label, key=f"cancel_{task['id']}", help="取消此任务"):
                        try:
                            resp = logged_post(
                                f"{API_BASE_URL}/tasks/{task['id']}/cancel",
                                headers=build_headers(),
                                timeout=10,
                                operation_name="tasks.cancel",
                            )
                            if resp.status_code == 200:
                                success_msg("✅ 任务已取消，状态已更新为「已取消」")
                                st.rerun()
                            else:
                                data = resp.json() if resp.content else {}
                                err_business(data.get("detail") or "取消失败（任务可能已在执行中）")
                        except Exception as e:
                            err_network(str(e))
                
                # 显示已取消状态确认
                if status == "cancelled":
                    st.caption("🚫 此任务已被取消")


if __name__ == "__main__":
    main()
