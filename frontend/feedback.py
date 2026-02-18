"""
前端统一反馈：加载态、错误提示、成功反馈（Phase 2.2 体验优化）。

使用方式：
  from feedback import loading, err_network, err_timeout, err_server, err_business, success_expired
  with loading("正在加载..."):
      ...
  if error: err_network()
"""

from contextlib import contextmanager
from typing import Generator

import streamlit as st

# 统一文案，便于后续与 R4 规范对齐
MSG_NETWORK = "无法连接到服务器，请检查后端服务是否启动"
MSG_TIMEOUT = "请求超时，请稍后重试"
MSG_SERVER = "服务暂时不可用，请稍后重试"
MSG_LOGIN_EXPIRED = "登录已过期，请重新登录"


@contextmanager
def loading(message: str = "请稍候...") -> Generator[None, None, None]:
    """统一加载态：在异步操作外使用 with loading('...'):"""
    with st.spinner(message):
        yield


def err_network() -> None:
    st.error("❌ " + MSG_NETWORK)


def err_timeout() -> None:
    st.error("❌ " + MSG_TIMEOUT)


def err_server(detail: str = "") -> None:
    msg = MSG_SERVER
    if detail:
        msg += f"（{detail}）"
    st.error("❌ " + msg)


def err_business(message: str) -> None:
    st.error("❌ " + message)


def success_expired() -> None:
    st.error("❌ " + MSG_LOGIN_EXPIRED)


def success_msg(message: str) -> None:
    st.success("✅ " + message)


def warn_msg(message: str) -> None:
    st.warning("⚠️ " + message)
