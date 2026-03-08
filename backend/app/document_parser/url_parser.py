"""URL parser: fetch page and extract main content text."""

import re
from pathlib import Path

import requests
from readability import Document as ReadabilityDocument

from app.document_parser.base import BaseDocumentParser
from app.document_parser.models import ContentType, ParsedContent


class UrlParser(BaseDocumentParser):
    """Fetch URL and extract main body text. file_path is treated as URL string."""

    def parse(self, file_path: Path) -> list[ParsedContent]:
        """Parse URL and return extracted content."""
        url = str(file_path) if file_path else ""
        return self.parse_url(url)

    def parse_url(self, url: str) -> list[ParsedContent]:
        """Fetch URL and return extracted content as ParsedContent list."""
        url = (url or "").strip()
        if not url.startswith(("http://", "https://")):
            return [
                ParsedContent(
                    content_type=ContentType.TEXT,
                    text="（无效的 URL）",
                    metadata={"error": "invalid_url", "url": url},
                )
            ]
        try:
            resp = requests.get(
                url,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (compatible; EnterpriseRAG/1.0)"},
            )
            resp.raise_for_status()
            doc = ReadabilityDocument(resp.text)
            title = doc.title() or ""
            body = doc.summary()
            if not body:
                text = title or "（未能提取正文）"
            else:
                text = re.sub(r"<[^>]+>", " ", body)
                text = re.sub(r"\s+", " ", text).strip()
                text = f"{title}\n\n{text}" if title else text

            return [
                ParsedContent(
                    content_type=ContentType.TEXT,
                    text=text,
                    metadata={
                        "source_url": url,
                        "title": title,
                    },
                )
            ]
        except requests.RequestException as e:
            return [
                ParsedContent(
                    content_type=ContentType.TEXT,
                    text=f"（抓取失败: {e}）",
                    metadata={"error": str(e), "url": url},
                )
            ]
        except Exception as e:
            return [
                ParsedContent(
                    content_type=ContentType.TEXT,
                    text=f"（解析失败: {e}）",
                    metadata={"error": str(e), "url": url},
                )
            ]

    def parse_url_text(self, url: str) -> str:
        """Fetch URL and return extracted main text (backward compatibility)."""
        contents = self.parse_url(url)
        return contents[0].text if contents else ""
