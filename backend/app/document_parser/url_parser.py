"""URL parser: fetch page and extract main content text."""

import re
from pathlib import Path

import requests
from readability import Document as ReadabilityDocument

from app.document_parser.base import BaseDocumentParser


class UrlParser(BaseDocumentParser):
    """Fetch URL and extract main body text. file_path is treated as URL string."""

    def parse_url(self, url: str) -> str:
        """Fetch URL and return extracted main text. Use this when doc.file_path is the URL string."""
        url = (url or "").strip()
        if not url.startswith(("http://", "https://")):
            return "（无效的 URL）"
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (compatible; EnterpriseRAG/1.0)"})
            resp.raise_for_status()
            doc = ReadabilityDocument(resp.text)
            title = doc.title() or ""
            body = doc.summary()
            if not body:
                return title or "（未能提取正文）"
            text = re.sub(r"<[^>]+>", " ", body)
            text = re.sub(r"\s+", " ", text).strip()
            return f"{title}\n\n{text}" if title else text
        except requests.RequestException as e:
            return f"（抓取失败: {e}）"
        except Exception as e:
            return f"（解析失败: {e}）"

    def parse(self, file_path: Path) -> str:
        url = str(file_path) if file_path else ""
        return self.parse_url(url)
