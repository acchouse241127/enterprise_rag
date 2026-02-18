"""Login page for Enterprise RAG System."""

import os

import requests
import streamlit as st

from feedback import err_business, err_network, err_timeout, loading, success_msg
from operation_log import logged_post

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

st.title("🔐 登录")

# 显示当前登录状态
if st.session_state.get("access_token"):
    st.success("✅ 您已登录")
    if st.button("退出登录", type="secondary"):
        del st.session_state["access_token"]
        st.rerun()
    st.stop()

st.caption("使用用户名、密码和 TOTP 进行登录")

with st.form("login_form"):
    username = st.text_input("用户名", placeholder="请输入用户名")
    password = st.text_input("密码", type="password", placeholder="请输入密码")
    totp_code = st.text_input("TOTP 验证码", max_chars=6, placeholder="如已绑定 TOTP，请输入 6 位验证码")
    submitted = st.form_submit_button("登录", type="primary", use_container_width=True)

if submitted:
    if not username.strip():
        st.error("请输入用户名")
        st.stop()
    if not password:
        st.error("请输入密码")
        st.stop()

    payload = {
        "username": username.strip(),
        "password": password,
        "totp_code": totp_code.strip() if totp_code.strip() else None,
    }

    with loading("正在登录..."):
        try:
            response = logged_post(
                f"{API_BASE_URL}/auth/login",
                json=payload,
                timeout=10,
                operation_name="auth.login",
            )
            data = response.json()
        except requests.exceptions.ConnectionError:
            err_network()
        except requests.exceptions.Timeout:
            err_timeout()
        except Exception as exc:  # noqa: BLE001
            err_business(f"请求失败：{exc}")
        else:
            if data.get("code") == 0:
                token = data.get("data", {}).get("access_token")
                st.session_state["access_token"] = token
                success_msg("登录成功！")
                st.balloons()
                st.info("请从左侧菜单选择功能页面")
            else:
                err_business(data.get("detail") or data.get("message") or "登录失败")

st.divider()
st.markdown("""
### 测试账号

| 用户名 | 密码 | TOTP |
|--------|------|------|
| admin | password123 | 无需 |
| admin_totp | password123 | 需要 |
""")

