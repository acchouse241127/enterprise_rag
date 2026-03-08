"""
Unit tests for URL parser.

Tests for app/document_parser/url_parser.py
Author: C2
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.document_parser.models import ContentType


class TestUrlParser:
    """Tests for UrlParser class."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()
        assert parser is not None

    def test_parse_url_valid(self):
        """Test parsing a valid URL."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><head><title>Test Page</title></head><body><p>Main content here</p></body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = "Test Page"
                mock_doc.summary.return_value = "<p>Main content here</p>"
                MockDoc.return_value = mock_doc

                contents = parser.parse_url("https://example.com")
                assert len(contents) == 1
                assert contents[0].content_type == ContentType.TEXT
                assert "Test Page" in contents[0].text
                assert "Main content here" in contents[0].text

    def test_parse_url_invalid_scheme(self):
        """Test parsing URL without http/https scheme."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        contents = parser.parse_url("ftp://example.com")
        assert len(contents) == 1
        assert "无效的 URL" in contents[0].text

    def test_parse_url_empty(self):
        """Test parsing empty URL."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        contents = parser.parse_url("")
        assert len(contents) == 1
        assert "无效的 URL" in contents[0].text

    def test_parse_url_whitespace(self):
        """Test parsing URL with only whitespace."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        contents = parser.parse_url("   ")
        assert len(contents) == 1
        assert "无效的 URL" in contents[0].text

    def test_parse_url_strips_whitespace(self):
        """Test that URL whitespace is stripped."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = ""
                mock_doc.summary.return_value = "<p>Content</p>"
                MockDoc.return_value = mock_doc

                parser.parse_url("  https://example.com  ")

                # Verify URL was stripped before being passed to requests.get
                call_args = mock_get.call_args[0][0]
                assert call_args == "https://example.com"

    def test_parse_url_http_scheme(self):
        """Test parsing URL with http scheme."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><body>HTTP content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = "HTTP Page"
                mock_doc.summary.return_value = "<p>HTTP content</p>"
                MockDoc.return_value = mock_doc

                contents = parser.parse_url("http://example.com")
                assert "HTTP Page" in contents[0].text

    def test_parse_url_request_exception(self):
        """Test handling of request exceptions."""
        from app.document_parser.url_parser import UrlParser
        import requests

        parser = UrlParser()

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException("Connection error")

            contents = parser.parse_url("https://example.com")
            assert "抓取失败" in contents[0].text

    def test_parse_url_timeout_exception(self):
        """Test handling of timeout exceptions."""
        from app.document_parser.url_parser import UrlParser
        import requests

        parser = UrlParser()

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.Timeout("Request timed out")

            contents = parser.parse_url("https://example.com")
            assert "抓取失败" in contents[0].text

    def test_parse_url_parsing_exception(self):
        """Test handling of parsing exceptions."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                MockDoc.side_effect = Exception("Parse error")

                contents = parser.parse_url("https://example.com")
                assert "解析失败" in contents[0].text

    def test_parse_url_no_title(self):
        """Test parsing URL when page has no title."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><body>Just content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = ""
                mock_doc.summary.return_value = "<p>Just content</p>"
                MockDoc.return_value = mock_doc

                contents = parser.parse_url("https://example.com")
                assert "Just content" in contents[0].text

    def test_parse_url_no_body(self):
        """Test parsing URL when page has no body content."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><head><title>Title Only</title></head></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = "Title Only"
                mock_doc.summary.return_value = ""
                MockDoc.return_value = mock_doc

                contents = parser.parse_url("https://example.com")
                assert "Title Only" in contents[0].text

    def test_parse_url_no_title_no_body(self):
        """Test parsing URL when page has no title and no body."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = ""
                mock_doc.summary.return_value = ""
                MockDoc.return_value = mock_doc

                contents = parser.parse_url("https://example.com")
                assert "未能提取正文" in contents[0].text

    def test_parse_url_strips_html_tags(self):
        """Test that HTML tags are stripped from body."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = "Test"
                mock_doc.summary.return_value = "<div><p><strong>Bold</strong> text</p></div>"
                MockDoc.return_value = mock_doc

                contents = parser.parse_url("https://example.com")
                assert "<div>" not in contents[0].text
                assert "<p>" not in contents[0].text
                assert "<strong>" not in contents[0].text

    def test_parse_url_user_agent_header(self):
        """Test that custom User-Agent is sent."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = ""
                mock_doc.summary.return_value = "<p>Content</p>"
                MockDoc.return_value = mock_doc

                parser.parse_url("https://example.com")

                call_kwargs = mock_get.call_args[1]
                assert "User-Agent" in call_kwargs.get("headers", {})
                assert "EnterpriseRAG" in call_kwargs["headers"]["User-Agent"]

    def test_parse_url_timeout_value(self):
        """Test that timeout is set correctly."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = ""
                mock_doc.summary.return_value = "<p>Content</p>"
                MockDoc.return_value = mock_doc

                parser.parse_url("https://example.com")

                call_kwargs = mock_get.call_args[1]
                assert call_kwargs.get("timeout") == 15

    def test_parse_method_with_url_string(self):
        """Test parse method with URL string (not Path object)."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = "Test"
                mock_doc.summary.return_value = "<p>Content</p>"
                MockDoc.return_value = mock_doc

                # parse() expects a Path but treats it as URL string
                contents = parser.parse_url("https://example.com")
                assert "Test" in contents[0].text

    def test_parse_url_normalizes_whitespace(self):
        """Test that whitespace is normalized in extracted text."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = ""
                # Multiple spaces and newlines
                mock_doc.summary.return_value = "<p>Text   with    multiple    spaces</p>"
                MockDoc.return_value = mock_doc

                contents = parser.parse_url("https://example.com")
                # Multiple spaces should be normalized
                assert "    " not in contents[0].text

    def test_parse_url_text_backward_compat(self):
        """Test parse_url_text returns plain string for backward compatibility."""
        from app.document_parser.url_parser import UrlParser

        parser = UrlParser()

        mock_response = MagicMock()
        mock_response.text = "<html><head><title>Test</title></head><body><p>Content</p></body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_response):
            with patch("app.document_parser.url_parser.ReadabilityDocument") as MockDoc:
                mock_doc = MagicMock()
                mock_doc.title.return_value = "Test"
                mock_doc.summary.return_value = "<p>Content</p>"
                MockDoc.return_value = mock_doc

                text = parser.parse_url_text("https://example.com")
                assert isinstance(text, str)
                assert "Test" in text
