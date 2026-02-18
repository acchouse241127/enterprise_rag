"""
Conversation management page - export and share.

Phase 3.3: 对话导出与分享
Author: C2
Date: 2026-02-14
"""

import os
from datetime import datetime

import requests
import streamlit as st

from feedback import err_business, err_network, success_msg
from operation_log import logged_get, logged_post, logged_delete

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


def fetch_conversations(knowledge_base_id: int | None = None) -> list[dict]:
    """Fetch user's conversations."""
    try:
        params = {}
        if knowledge_base_id:
            params["knowledge_base_id"] = knowledge_base_id
        resp = logged_get(
            f"{API_BASE_URL}/conversations",
            headers=build_headers(),
            params=params,
            timeout=10,
            operation_name="conversations.list",
        )
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception:
        return []


def fetch_knowledge_bases() -> list[dict]:
    """Fetch knowledge bases."""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/knowledge-bases",
            headers=build_headers(),
            timeout=10,
            operation_name="knowledge-bases.list",
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", [])
        return []
    except Exception:
        return []


def main():
    st.set_page_config(page_title="对话管理", page_icon="💬", layout="wide")
    st.title("💬 对话管理")

    # 模块使用说明（精华）
    with st.container(border=True):
        st.markdown("**📌 使用说明**")
        st.markdown("查看在「RAG 问答」中产生的历史对话。支持：**导出**为 MD/PDF/Word；**生成分享链接**供他人免登录查看；**删除**不需要的对话。")
        st.caption("💡 左侧可按知识库筛选。导出或分享后，可在对应入口下载文件或复制链接。")

    if not check_auth():
        return

    st.markdown("---")

    # Sidebar filters
    with st.sidebar:
        st.subheader("筛选条件")
        kbs = fetch_knowledge_bases()
        kb_options = {"全部": None}
        kb_options.update({kb["name"]: kb["id"] for kb in kbs})
        selected_kb_name = st.selectbox("知识库", list(kb_options.keys()))
        selected_kb_id = kb_options[selected_kb_name]

    # Fetch conversations
    conversations = fetch_conversations(selected_kb_id)

    if not conversations:
        st.info("📭 暂无对话记录")
        st.caption("在 RAG 问答页面进行对话后，对话记录将显示在这里")
        return

    # Display conversations
    st.subheader(f"📋 对话列表（共 {len(conversations)} 条）")

    for conv in conversations:
        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 2, 2])

            with col1:
                title = conv.get("title") or f"对话 {conv['conversation_id'][:8]}"
                st.markdown(f"**{title}**")
                st.caption(f"ID: `{conv['conversation_id'][:20]}...`  |  📅 {conv.get('created_at', '')[:19].replace('T', ' ') if conv.get('created_at') else '-'}")

            with col2:
                if conv.get("is_shared"):
                    st.success("🔗 已分享")
                    if conv.get("share_expires_at"):
                        st.caption(f"过期: {conv['share_expires_at'][:10]}")
                else:
                    st.info("🔒 未分享")

            with col3:
                conv_id = conv["id"]
                export_col1, export_col2, export_col3 = st.columns(3)
                with export_col1:
                    if st.button("📄 MD", key=f"export_md_{conv_id}", help="导出 Markdown"):
                        try:
                            resp = requests.get(
                                f"{API_BASE_URL}/conversations/{conv_id}/export/markdown",
                                headers=build_headers(),
                                timeout=30,
                            )
                            if resp.status_code == 200:
                                filename = f"conversation_{conv['conversation_id'][:8]}.md"
                                st.download_button(
                                    "⬇️ 下载 MD",
                                    data=resp.content,
                                    file_name=filename,
                                    mime="text/markdown",
                                    key=f"dl_md_{conv_id}",
                                )
                            else:
                                err_business("导出失败")
                        except Exception as e:
                            err_network(str(e))

                with export_col2:
                    if st.button("📕 PDF", key=f"export_pdf_{conv_id}", help="导出 PDF"):
                        try:
                            resp = requests.get(
                                f"{API_BASE_URL}/conversations/{conv_id}/export/pdf",
                                headers=build_headers(),
                                timeout=30,
                            )
                            if resp.status_code == 200:
                                filename = f"conversation_{conv['conversation_id'][:8]}.pdf"
                                st.download_button(
                                    "⬇️ 下载 PDF",
                                    data=resp.content,
                                    file_name=filename,
                                    mime="application/pdf",
                                    key=f"dl_pdf_{conv_id}",
                                )
                            else:
                                err_business("导出失败")
                        except Exception as e:
                            err_network(str(e))

                with export_col3:
                    if st.button("📘 DOCX", key=f"export_docx_{conv_id}", help="导出 Word"):
                        try:
                            resp = requests.get(
                                f"{API_BASE_URL}/conversations/{conv_id}/export/docx",
                                headers=build_headers(),
                                timeout=30,
                            )
                            if resp.status_code == 200:
                                filename = f"conversation_{conv['conversation_id'][:8]}.docx"
                                st.download_button(
                                    "⬇️ 下载 DOCX",
                                    data=resp.content,
                                    file_name=filename,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"dl_docx_{conv_id}",
                                )
                            else:
                                err_business("导出失败")
                        except Exception as e:
                            err_network(str(e))

                # Share toggle
                share_col1, share_col2 = st.columns(2)
                with share_col1:
                    if not conv.get("is_shared"):
                        if st.button("🔗 分享", key=f"share_{conv_id}"):
                            try:
                                resp = logged_post(
                                    f"{API_BASE_URL}/conversations/{conv_id}/share",
                                    headers=build_headers(),
                                    json={"expires_in_days": 7},
                                    timeout=10,
                                    operation_name="conversations.share",
                                )
                                if resp.status_code == 200:
                                    data = resp.json()
                                    success_msg(f"分享链接已生成")
                                    st.code(data.get("share_url", ""))
                                    st.rerun()
                                else:
                                    err_business("分享失败")
                            except Exception as e:
                                err_network(str(e))
                    else:
                        if st.button("🔒 取消", key=f"unshare_{conv_id}"):
                            try:
                                resp = logged_delete(
                                    f"{API_BASE_URL}/conversations/{conv_id}/share",
                                    headers=build_headers(),
                                    timeout=10,
                                    operation_name="conversations.unshare",
                                )
                                if resp.status_code == 200:
                                    success_msg("已取消分享")
                                    st.rerun()
                                else:
                                    err_business("取消失败")
                            except Exception as e:
                                err_network(str(e))

                with share_col2:
                    if st.button("🗑️ 删除", key=f"delete_{conv_id}"):
                        try:
                            resp = logged_delete(
                                f"{API_BASE_URL}/conversations/{conv_id}",
                                headers=build_headers(),
                                timeout=10,
                                operation_name="conversations.delete",
                            )
                            if resp.status_code == 200:
                                success_msg("对话已删除")
                                st.rerun()
                            else:
                                err_business("删除失败")
                        except Exception as e:
                            err_network(str(e))

                # Show share link if shared
                if conv.get("is_shared") and conv.get("share_token"):
                    st.text_input(
                        "分享链接",
                        value=f"/share/{conv['share_token']}",
                        key=f"share_link_{conv_id}",
                        disabled=True,
                    )


if __name__ == "__main__":
    main()
