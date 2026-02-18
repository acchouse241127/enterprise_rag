#!/usr/bin/env python3
"""
测试 Kimi K2.5（月之暗面 Moonshot）LLM 连接是否正常。
使用与后端相同的 .env 配置，直接调用 OpenAI 兼容接口。
用法：在项目根目录或 enterprise_rag 目录下执行
  python scripts/test_llm_kimi.py
  或
  cd enterprise_rag && python scripts/test_llm_kimi.py
"""

from __future__ import annotations

import os
import sys

# 确保能加载 .env：优先 enterprise_rag/.env
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, ".env")
if not os.path.isfile(ENV_PATH):
    ENV_PATH = os.path.join(os.path.dirname(ROOT), "enterprise_rag", ".env")
if os.path.isfile(ENV_PATH):
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)

import httpx


def main() -> None:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = (os.getenv("LLM_BASE_URL", "https://api.moonshot.cn/v1") or "").rstrip("/")
    model = os.getenv("LLM_MODEL_NAME", "kimi-k2.5").strip()
    timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

    if not api_key:
        print("[FAIL] LLM_API_KEY not set in .env")
        sys.exit(1)

    url = f"{base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    # Kimi K2.5 仅支持 temperature=1，其他模型可用 0.2
    temperature = 1.0 if "kimi-k2" in model.lower() else 0.2
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "请用一句话介绍你自己。"},
        ],
        "temperature": temperature,
        "max_tokens": 200,
    }

    print("Testing LLM connection...")
    print(f"  BASE_URL: {base_url}")
    print(f"  MODEL:    {model}")
    print()

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        if content:
            print("[OK] LLM connection success, Kimi K2.5 responded.")
            print()
            print("Reply:")
            print("-" * 40)
            print(content.strip())
            print("-" * 40)
        else:
            print("[WARN] HTTP 200 but no content in response.")
    except httpx.HTTPStatusError as e:
        print("[FAIL] Request failed HTTP", e.response.status_code)
        try:
            err = e.response.json()
            print("   Error body:", err)
        except Exception:
            print("   Response text:", (e.response.text or "")[:500])
        sys.exit(1)
    except httpx.RequestError as e:
        print("[FAIL] Network/connection error:", e)
        sys.exit(1)
    except Exception as e:
        print("[FAIL] Exception:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
