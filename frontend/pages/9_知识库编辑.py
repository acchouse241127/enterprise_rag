"""
Knowledge base editing page - content and chunk settings.

Phase 3.3: 知识库在线编辑与分块调整
Author: C2
Date: 2026-02-14
"""

import os

import streamlit as st

from feedback import err_business, err_network, success_msg
from operation_log import logged_get, logged_post, logged_put

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


def fetch_documents(kb_id: int) -> list[dict]:
    """Fetch documents in a knowledge base."""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/knowledge-bases/{kb_id}/documents",
            headers=build_headers(),
            timeout=10,
            operation_name="documents.list",
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", [])
        return []
    except Exception:
        return []


def fetch_chunk_settings(kb_id: int) -> dict | None:
    """Fetch chunk settings for a knowledge base."""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/knowledge-bases/{kb_id}/chunk-settings",
            headers=build_headers(),
            timeout=10,
            operation_name="kb.chunk-settings.get",
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def fetch_document_content(doc_id: int) -> dict | None:
    """Fetch document content."""
    try:
        resp = logged_get(
            f"{API_BASE_URL}/knowledge-bases/documents/{doc_id}/content",
            headers=build_headers(),
            timeout=30,
            operation_name="documents.content.get",
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def main():
    st.set_page_config(page_title="知识库编辑", page_icon="✏️", layout="wide")
    st.title("✏️ 知识库在线编辑")
    st.caption("编辑文档内容、调整分块参数")

    if not check_auth():
        return

    # Fetch knowledge bases
    kbs = fetch_knowledge_bases()
    if not kbs:
        st.warning("暂无知识库，请先创建知识库")
        return

    # Knowledge base selector
    kb_options = {kb["name"]: kb["id"] for kb in kbs}
    selected_kb_name = st.selectbox("选择知识库", list(kb_options.keys()))
    selected_kb_id = kb_options[selected_kb_name]

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📄 文档编辑", "⚙️ 分块设置", "🔄 批量重分块"])

    # ============== Tab 1: Document Editing ==============
    with tab1:
        st.subheader("文档内容编辑")

        documents = fetch_documents(selected_kb_id)
        if not documents:
            st.info("该知识库暂无文档")
        else:
            doc_options = {f"{d.get('title', d['filename'])} ({d['filename']})": d["id"] for d in documents}
            selected_doc_label = st.selectbox("选择文档", list(doc_options.keys()))
            selected_doc_id = doc_options[selected_doc_label]

            # Fetch document content
            doc_data = fetch_document_content(selected_doc_id)
            if doc_data:
                st.caption(f"文档状态: {doc_data.get('status', 'unknown')}")
                if doc_data.get("parser_message"):
                    st.caption(f"解析信息: {doc_data['parser_message']}")

                # Content editor
                content = doc_data.get("content", "")
                edited_content = st.text_area(
                    "文档内容",
                    value=content,
                    height=400,
                    key=f"content_editor_{selected_doc_id}",
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 保存并重新向量化", type="primary", use_container_width=True):
                        if edited_content.strip():
                            try:
                                resp = logged_put(
                                    f"{API_BASE_URL}/knowledge-bases/documents/{selected_doc_id}/content",
                                    headers=build_headers(),
                                    json={"content": edited_content},
                                    timeout=60,
                                    operation_name="documents.content.update",
                                )
                                if resp.status_code == 200:
                                    data = resp.json()
                                    success_msg(data.get("message", "保存成功"))
                                else:
                                    err_business(resp.json().get("detail", "保存失败"))
                            except Exception as e:
                                err_network(str(e))
                        else:
                            err_business("内容不能为空")

                with col2:
                    if st.button("🔄 仅重新分块", use_container_width=True):
                        try:
                            resp = logged_post(
                                f"{API_BASE_URL}/knowledge-bases/documents/{selected_doc_id}/rechunk",
                                headers=build_headers(),
                                json={},
                                timeout=60,
                                operation_name="documents.rechunk",
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                success_msg(data.get("message", "重分块成功"))
                            else:
                                err_business(resp.json().get("detail", "重分块失败"))
                        except Exception as e:
                            err_network(str(e))
            else:
                st.error("无法获取文档内容")

    # ============== Tab 2: Chunk Settings ==============
    with tab2:
        st.subheader("分块参数设置")
        st.caption("调整知识库的分块参数，影响后续上传的文档和重分块操作")

        chunk_settings = fetch_chunk_settings(selected_kb_id)
        if chunk_settings:
            col1, col2 = st.columns(2)

            with col1:
                st.metric("当前 chunk_size", chunk_settings.get("chunk_size", 500))
                st.metric("当前 chunk_overlap", chunk_settings.get("chunk_overlap", 50))

            with col2:
                defaults = chunk_settings.get("global_defaults", {})
                st.caption(f"全局默认: size={defaults.get('chunk_size', 500)}, overlap={defaults.get('chunk_overlap', 50)}")
                if chunk_settings.get("is_custom"):
                    st.info("✅ 使用自定义参数")
                else:
                    st.info("📋 使用全局默认参数")

            st.divider()

            # Update form
            with st.form("chunk_settings_form"):
                st.markdown("**修改分块参数**")

                new_chunk_size = st.number_input(
                    "chunk_size（字符数）",
                    min_value=100,
                    max_value=10000,
                    value=chunk_settings.get("chunk_size", 500),
                    step=100,
                    help="每个文本块的目标大小（100-10000）",
                )

                new_chunk_overlap = st.number_input(
                    "chunk_overlap（字符数）",
                    min_value=0,
                    max_value=500,
                    value=chunk_settings.get("chunk_overlap", 50),
                    step=10,
                    help="相邻块之间的重叠字符数（0-500）",
                )

                use_default = st.checkbox("使用全局默认值", value=not chunk_settings.get("is_custom"))

                submitted = st.form_submit_button("保存设置", type="primary", use_container_width=True)

                if submitted:
                    try:
                        payload = {}
                        if not use_default:
                            payload["chunk_size"] = new_chunk_size
                            payload["chunk_overlap"] = new_chunk_overlap
                        # If use_default is True, send None values to reset to defaults

                        resp = logged_put(
                            f"{API_BASE_URL}/knowledge-bases/{selected_kb_id}/chunk-settings",
                            headers=build_headers(),
                            json=payload,
                            timeout=10,
                            operation_name="kb.chunk-settings.update",
                        )
                        if resp.status_code == 200:
                            success_msg("分块参数已更新")
                            st.rerun()
                        else:
                            err_business(resp.json().get("detail", "更新失败"))
                    except Exception as e:
                        err_network(str(e))
        else:
            st.error("无法获取分块设置")

    # ============== Tab 3: Batch Rechunk ==============
    with tab3:
        st.subheader("批量重分块")
        st.caption("使用当前知识库的分块参数，重新分块所有文档")

        st.warning("⚠️ 此操作会重新处理所有文档，可能需要较长时间")

        documents = fetch_documents(selected_kb_id)
        st.info(f"该知识库共有 {len(documents)} 个文档")

        if st.button("🔄 开始批量重分块", type="primary", use_container_width=True):
            with st.spinner("正在重分块所有文档..."):
                try:
                    resp = logged_post(
                        f"{API_BASE_URL}/knowledge-bases/{selected_kb_id}/rechunk-all",
                        headers=build_headers(),
                        timeout=300,
                        operation_name="kb.rechunk-all",
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        success_count = data.get("success_count", 0)
                        failed_count = data.get("failed_count", 0)
                        success_msg(f"重分块完成：成功 {success_count} 个，失败 {failed_count} 个")
                    else:
                        err_business(resp.json().get("detail", "重分块失败"))
                except Exception as e:
                    err_network(str(e))


if __name__ == "__main__":
    main()
