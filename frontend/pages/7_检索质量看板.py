"""Retrieval quality dashboard page.

Phase 3.2: 检索质量看板
Author: C2
Date: 2026-02-13
"""

import os
from datetime import datetime, timedelta

import streamlit as st

from feedback import err_business, loading, success_msg
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


@st.cache_data(ttl=10, show_spinner=False)
def fetch_retrieval_stats(kb_id: int | None, start_date: str | None, end_date: str | None, token: str) -> dict:
    """Fetch retrieval statistics. TTL=10s so 刷新 shows new data soon after QA."""
    params = {}
    if kb_id:
        params["knowledge_base_id"] = kb_id
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    try:
        resp = logged_get(
            f"{API_BASE_URL}/retrieval/stats",
            params=params,
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=15,
            operation_name="retrieval.stats",
        )
        if resp.status_code == 401:
            return {"_auth_required": True}
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {})
    except Exception:
        pass
    return {}


@st.cache_data(ttl=10, show_spinner=False)
def fetch_stats_by_date(kb_id: int | None, days: int, token: str) -> list:
    """Fetch daily statistics."""
    params = {"days": days}
    if kb_id:
        params["knowledge_base_id"] = kb_id
    try:
        resp = logged_get(
            f"{API_BASE_URL}/retrieval/stats/by-date",
            params=params,
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=15,
            operation_name="retrieval.stats.by-date",
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", [])
    except Exception:
        pass
    return []


@st.cache_data(ttl=15, show_spinner=False)
def fetch_retrieval_logs(
    kb_id: int | None,
    has_feedback: bool | None,
    feedback_type: str | None,
    limit: int,
    offset: int,
    token: str,
) -> tuple[list, int]:
    """Fetch retrieval logs."""
    params = {"limit": limit, "offset": offset}
    if kb_id:
        params["knowledge_base_id"] = kb_id
    if has_feedback is not None:
        params["has_feedback"] = has_feedback
    if feedback_type:
        params["feedback_type"] = feedback_type
    try:
        resp = logged_get(
            f"{API_BASE_URL}/retrieval/logs",
            params=params,
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=15,
            operation_name="retrieval.logs.list",
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("items", []), data.get("data", {}).get("total", 0)
    except Exception:
        pass
    return [], 0


@st.cache_data(ttl=8, show_spinner=False)
def fetch_knowledge_bases(token: str) -> list:
    """Fetch knowledge bases for filter dropdown."""
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


# ========== 侧边栏 ==========
with st.sidebar:
    st.title("🏠 Enterprise RAG")
    username = st.session_state.get("username", "用户")
    st.markdown(f"👤 **{username}**")
    if st.button("🚪 登出", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()
    st.caption("📊 检索质量看板")

# ========== 主内容区 ==========
st.title("📊 检索质量看板")

if not check_auth():
    st.stop()

token = st.session_state.get("access_token", "")

# ========== 筛选器 ==========
st.subheader("🔍 筛选条件")
col_kb, col_days, col_refresh = st.columns([2, 1, 1])

with col_kb:
    kbs = fetch_knowledge_bases(token)
    kb_options = {"全部知识库": None}
    kb_options.update({kb["name"]: kb["id"] for kb in kbs})
    selected_kb_name = st.selectbox("知识库", options=list(kb_options.keys()))
    selected_kb_id = kb_options[selected_kb_name]

with col_days:
    days_options = {"7 天": 7, "14 天": 14, "30 天": 30}
    selected_days_label = st.selectbox("时间范围", options=list(days_options.keys()))
    selected_days = days_options[selected_days_label]

with col_refresh:
    st.write("")
    st.write("")
    if st.button("🔄 刷新", use_container_width=True):
        fetch_retrieval_stats.clear()
        fetch_stats_by_date.clear()
        fetch_retrieval_logs.clear()
        st.rerun()

st.divider()

# ========== 统计指标卡片 ==========
st.subheader("📈 核心指标")

with loading("加载统计数据..."):
    stats = fetch_retrieval_stats(selected_kb_id, None, None, token)

# 鉴权失败时提示重新登录
if stats.get("_auth_required"):
    st.warning("⚠️ 登录已过期，请重新登录后刷新本页。")
    st.page_link("pages/1_登录.py", label="前往登录", icon="🔐")
    st.stop()

# 检索后仍无数据时给出提示
if stats.get("total_queries", 0) == 0 and stats.get("retrieval_log_enabled") is True:
    st.info(
        "💡 **完成 RAG 问答后**，请点击上方「🔄 刷新」查看统计（缓存约 10 秒）。"
        "若仍无数据，请检查后端日志是否有 `retrieval_log create failed`，或确认 .env 中未设置 RETRIEVAL_LOG_ENABLED=false。"
    )
elif stats.get("total_queries", 0) == 0 and stats.get("retrieval_log_enabled") is False:
    st.warning("⚠️ 检索日志未启用（RETRIEVAL_LOG_ENABLED=false），看板无数据。请在后端 .env 中设置 RETRIEVAL_LOG_ENABLED=true 并重启后端。")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📝 总查询数",
        value=stats.get("total_queries", 0),
    )

with col2:
    avg_score = stats.get("avg_top_score")
    st.metric(
        label="⭐ 平均最高分",
        value=f"{avg_score:.3f}" if avg_score else "-",
    )

with col3:
    avg_time = stats.get("avg_response_time_ms")
    st.metric(
        label="⏱️ 平均响应时间",
        value=f"{avg_time:.0f} ms" if avg_time else "-",
    )

with col4:
    not_helpful_ratio = stats.get("not_helpful_ratio", 0)
    st.metric(
        label="👎 无用反馈率",
        value=f"{not_helpful_ratio:.1f}%",
        delta=None,
        delta_color="inverse",
    )

# 第二行指标
col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric(
        label="👍 有用反馈",
        value=stats.get("helpful_count", 0),
    )

with col6:
    st.metric(
        label="👎 无用反馈",
        value=stats.get("not_helpful_count", 0),
    )

with col7:
    st.metric(
        label="🔖 问题样本",
        value=stats.get("sample_count", 0),
    )

with col8:
    avg_chunks = stats.get("avg_chunks_returned")
    st.metric(
        label="📄 平均返回块数",
        value=f"{avg_chunks:.1f}" if avg_chunks else "-",
    )

st.divider()

# ========== 趋势图表 ==========
st.subheader("📉 查询趋势")

daily_stats = fetch_stats_by_date(selected_kb_id, selected_days, token)

if daily_stats:
    import pandas as pd

    df = pd.DataFrame(daily_stats)
    df["date"] = pd.to_datetime(df["date"])

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.caption("每日查询量")
        st.bar_chart(df.set_index("date")["query_count"])

    with col_chart2:
        st.caption("每日平均分数")
        if "avg_score" in df.columns:
            st.line_chart(df.set_index("date")["avg_score"])
        else:
            st.info("暂无分数数据")
else:
    st.info("📭 暂无趋势数据")

st.divider()

# ========== 检索日志列表 ==========
st.subheader("📜 检索日志")

col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    feedback_filter = st.selectbox(
        "反馈状态",
        options=["全部", "有反馈", "无反馈", "有用", "无用"],
    )
with col_filter2:
    page_size = st.selectbox("每页条数", options=[10, 20, 50], index=0)

# 解析筛选条件
has_feedback = None
feedback_type = None
if feedback_filter == "有反馈":
    has_feedback = True
elif feedback_filter == "无反馈":
    has_feedback = False
elif feedback_filter == "有用":
    feedback_type = "helpful"
elif feedback_filter == "无用":
    feedback_type = "not_helpful"

# 分页
if "log_page" not in st.session_state:
    st.session_state["log_page"] = 0

offset = st.session_state["log_page"] * page_size

logs, total = fetch_retrieval_logs(
    selected_kb_id, has_feedback, feedback_type, page_size, offset, token
)

st.caption(f"共 {total} 条记录")

if logs:
    for log in logs:
        log_id = log["id"]
        query = log["query"]
        top_score = log.get("top_chunk_score")
        total_time = log.get("total_time_ms")
        created_at = log.get("created_at", "")[:16]
        feedbacks = log.get("feedbacks", [])

        with st.container(border=True):
            col_q, col_stats, col_actions = st.columns([3, 2, 1])

            with col_q:
                st.markdown(f"**Q:** {query[:100]}{'...' if len(query) > 100 else ''}")
                st.caption(f"ID: {log_id} | 时间: {created_at}")

            with col_stats:
                score_str = f"{top_score:.3f}" if top_score else "-"
                time_str = f"{total_time} ms" if total_time else "-"
                chunks_str = log.get("chunks_after_rerank", "-")
                st.caption(f"最高分: {score_str} | 耗时: {time_str} | 块数: {chunks_str}")

                # 显示已有反馈
                if feedbacks:
                    feedback_icons = []
                    for fb in feedbacks:
                        if fb["feedback_type"] == "helpful":
                            feedback_icons.append("👍")
                        else:
                            feedback_icons.append("👎")
                        if fb.get("is_sample_marked"):
                            feedback_icons.append("🔖")
                    st.caption(f"反馈: {' '.join(feedback_icons)}")

            with col_actions:
                # 添加反馈按钮
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("👍", key=f"helpful_{log_id}", help="标记为有用"):
                        try:
                            resp = logged_post(
                                f"{API_BASE_URL}/retrieval/feedback",
                                json={"retrieval_log_id": log_id, "feedback_type": "helpful"},
                                headers=build_headers(),
                                timeout=10,
                                operation_name="retrieval.feedback.add",
                            )
                            if resp.json().get("code") == 0:
                                success_msg("已标记为有用")
                                fetch_retrieval_logs.clear()
                                fetch_retrieval_stats.clear()
                                st.rerun()
                        except Exception as e:
                            err_business(str(e))

                with col_btn2:
                    if st.button("👎", key=f"not_helpful_{log_id}", help="标记为无用"):
                        try:
                            resp = logged_post(
                                f"{API_BASE_URL}/retrieval/feedback",
                                json={"retrieval_log_id": log_id, "feedback_type": "not_helpful"},
                                headers=build_headers(),
                                timeout=10,
                                operation_name="retrieval.feedback.add",
                            )
                            if resp.json().get("code") == 0:
                                success_msg("已标记为无用")
                                fetch_retrieval_logs.clear()
                                fetch_retrieval_stats.clear()
                                st.rerun()
                        except Exception as e:
                            err_business(str(e))

    # 分页控件
    st.divider()
    col_prev, col_info, col_next = st.columns([1, 2, 1])
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    current_page = st.session_state["log_page"] + 1

    with col_prev:
        if st.button("⬅️ 上一页", disabled=current_page <= 1, use_container_width=True):
            st.session_state["log_page"] -= 1
            st.rerun()

    with col_info:
        st.markdown(f"<center>第 {current_page} / {total_pages} 页</center>", unsafe_allow_html=True)

    with col_next:
        if st.button("下一页 ➡️", disabled=current_page >= total_pages, use_container_width=True):
            st.session_state["log_page"] += 1
            st.rerun()

else:
    st.info("📭 暂无检索日志")
