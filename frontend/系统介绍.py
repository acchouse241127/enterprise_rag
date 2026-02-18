"""Streamlit application entrypoint - 系统介绍首页."""

import streamlit as st

st.set_page_config(
    page_title="Enterprise RAG System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 登录状态
if st.session_state.get("access_token"):
    st.success("✅ 已登录")
else:
    st.warning("⚠️ 未登录，请先前往「登录」页面进行认证")

st.markdown("---")
st.markdown("## 📖 系统介绍")
st.markdown("*企业知识库智能问答系统 — Enterprise RAG System*")
st.caption("基于 RAG 技术，将企业文档导入知识库后，可用自然语言提问并获得带引用来源的回答。")

st.markdown("---")

# 功能导航与各模块详细介绍
st.markdown("### 🧭 功能导航")
st.caption("请从左侧菜单选择功能页面")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("#### 🔐 登录")
        st.markdown("**做什么**：用户认证，支持账号密码 + TOTP 双因素。")
        st.markdown("**怎么用**：首次使用需先登录；登出后可重新认证。")
    with st.container(border=True):
        st.markdown("#### 📚 知识库管理")
        st.markdown("**做什么**：创建、查看、删除知识库。知识库是文档的容器，可按主题划分（如产品手册、培训资料）。")
        st.markdown("**怎么用**：创建知识库 → 在「文档上传」中为其上传文档 → 在「RAG 问答」中选择该知识库提问。")
    with st.container(border=True):
        st.markdown("#### 📄 文档上传")
        st.markdown("**做什么**：将文档上传到指定知识库，支持 TXT、PDF、Word、Excel、PPT、图片等。系统自动解析并建立向量索引。")
        st.markdown("**怎么用**：选择知识库 → 拖拽或选择文件 → 开始上传。等待解析状态变为「已向量化」后再提问。")

with col2:
    with st.container(border=True):
        st.markdown("#### 💬 RAG 问答")
        st.markdown("**做什么**：选择知识库后用自然语言提问，系统检索相关内容并生成回答，可标注引用来源。")
        st.markdown("**怎么用**：选择知识库 → 输入问题 → 点击「确认提问」。可设置回答风格、检索数量、流式输出等。")
    with st.container(border=True):
        st.markdown("#### 💬 对话管理")
        st.markdown("**做什么**：查看在 RAG 问答中产生的历史对话，支持导出为 MD/PDF/Word，或生成分享链接供他人免登录查看。")
        st.markdown("**怎么用**：进入页面查看对话列表 → 按需导出或分享。可按知识库筛选。")
    with st.container(border=True):
        st.markdown("#### 📊 检索看板 / ⚙️ 其他")
        st.markdown("**做什么**：检索看板展示检索质量统计；异步任务可查看后台任务进度；知识库编辑可调整分块参数。")
        st.markdown("**怎么用**：按需进入对应页面查看或配置。")

st.markdown("---")
st.markdown("### 🚀 快速开始")
st.markdown("""
1. **登录**：在「登录」页面完成认证  
2. **建库**：在「知识库管理」创建一个知识库  
3. **上传**：在「文档上传」上传相关文档，等待解析完成  
4. **提问**：在「RAG 问答」选择知识库并开始提问
""")

with st.expander("📎 支持的文档格式"):
    st.markdown("- **文本**：TXT、Markdown")
    st.markdown("- **Office**：Word (.docx)、Excel (.xlsx)、PPT (.pptx)")
    st.markdown("- **PDF**：文字型与扫描件（OCR）")
    st.markdown("- **图片**：PNG、JPG（OCR 识别）")

st.markdown("---")
st.caption("Enterprise RAG System v1.0.0 | 请从左侧菜单选择功能")
