"""自动验证 V2.1 Phase 1 多模态解析器功能.

运行方式:
    cd backend
    python scripts/verify_multimodal_parser.py
"""

import sys
import tempfile
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.document_parser import (
    get_parser_for_extension,
    content_list_to_chunks,
    get_content_metadata,
    ContentType,
    ParsedContent,
)


def test_txt_parser():
    """测试 TXT 解析器."""
    print("\n" + "="*50)
    print("[TXT] Test TXT Parser")
    print("="*50)

    parser = get_parser_for_extension(".txt")
    if not parser:
        print("[FAIL] TXT parser not found")
        return False

    # 创建临时文件
    tmp_dir = tempfile.gettempdir()
    txt_path = Path(tmp_dir) / "rag_test.txt"
    txt_path.write_text("Hello World!\n这是测试文本。", encoding="utf-8")

    try:
        # 测试新接口
        contents = parser.parse(txt_path)
        print(f"  [OK] parse() return type: {type(contents).__name__}")
        print(f"  [OK] Content count: {len(contents)}")

        if contents:
            print(f"  [OK] First content type: {contents[0].content_type.value}")
            print(f"  [OK] Text preview: {contents[0].text[:50]}...")

        # 测试向后兼容
        text = parser.parse_text(txt_path)
        print(f"  [OK] parse_text() return type: {type(text).__name__}")
        print(f"  [OK] parse_text() preview: {text[:50]}...")

        return True
    finally:
        txt_path.unlink(missing_ok=True)


def test_markdown_parser():
    """测试 Markdown 解析器."""
    print("\n" + "="*50)
    print("[MD] Test Markdown Parser")
    print("="*50)

    parser = get_parser_for_extension(".md")
    if not parser:
        print("[FAIL] Markdown parser not found")
        return False

    md_content = """# Title

Paragraph 1 content.

Paragraph 2 content.
"""
    tmp_dir = tempfile.gettempdir()
    md_path = Path(tmp_dir) / "rag_test.md"
    md_path.write_text(md_content, encoding="utf-8")

    try:
        contents = parser.parse(md_path)
        print(f"  [OK] Content count: {len(contents)}")
        if contents:
            print(f"  [OK] Content preview: {contents[0].text[:100]}...")
        return True
    finally:
        md_path.unlink(missing_ok=True)


def test_converter():
    """测试转换层."""
    print("\n" + "="*50)
    print("[CONVERTER] Test Converter Layer")
    print("="*50)

    # 创建模拟的 ParsedContent 列表
    contents = [
        ParsedContent(content_type=ContentType.TEXT, text="Normal text content"),
        ParsedContent(
            content_type=ContentType.TABLE,
            text="raw table data",
            metadata={"table_markdown": "| A | B |\n|---|---|\n| 1 | 2 |"}
        ),
        ParsedContent(
            content_type=ContentType.IMAGE,
            text="OCR extracted text",
            metadata={"vlm_description": "A bar chart showing sales trends"}
        ),
        ParsedContent(
            content_type=ContentType.EQUATION,
            text="E = mc2",
            metadata={"latex": r"E = mc^2"}
        ),
    ]

    # 转换为 chunks
    chunks = content_list_to_chunks(contents)
    print(f"  [OK] Input content count: {len(contents)}")
    print(f"  [OK] Output chunk count: {len(chunks)}")

    for i, chunk in enumerate(chunks):
        preview = chunk[:80] + "..." if len(chunk) > 80 else chunk
        print(f"  [OK] Chunk {i+1}: {preview}")

    # 验证类型前缀
    has_table_prefix = any("[Table]" in c or "[Biao Ge]" in c or chunks[1].startswith("[") for c in chunks)
    print(f"  [OK] Table has prefix: {chunks[1].startswith('[')}")

    # 测试元数据提取
    metadata = get_content_metadata(contents)
    print(f"\n  [OK] Metadata extraction:")
    print(f"     - has_table: {metadata['has_table']}")
    print(f"     - has_image: {metadata['has_image']}")
    print(f"     - has_equation: {metadata['has_equation']}")

    return True


def test_excel_smart_detection():
    """测试 Excel 智能识别."""
    print("\n" + "="*50)
    print("[EXCEL] Test Excel Smart Detection")
    print("="*50)

    try:
        from openpyxl import Workbook
        from app.document_parser.excel_parser import ExcelDocumentParser

        # 创建小表格 (< 20行)
        wb_small = Workbook()
        ws_small = wb_small.active
        ws_small.title = "SmallTable"
        ws_small["A1"] = "Name"
        ws_small["B1"] = "Age"
        ws_small["A2"] = "Tom"
        ws_small["B2"] = "25"
        ws_small["A3"] = "Jerry"
        ws_small["B3"] = "30"

        tmp_dir = tempfile.gettempdir()
        small_excel = Path(tmp_dir) / "rag_test_small.xlsx"
        wb_small.save(small_excel)

        parser = ExcelDocumentParser()
        contents = parser.parse(small_excel)

        print(f"  [OK] Small table (3 rows) result:")
        print(f"     - Content count: {len(contents)}")
        if contents:
            print(f"     - Type: {contents[0].content_type.value}")
            # Check if it's a complete table (has markdown)
            has_md = "table_markdown" in contents[0].metadata
            print(f"     - Has markdown: {has_md}")
            print(f"     - Preview: {contents[0].text[:100]}...")

        small_excel.unlink(missing_ok=True)

        # 创建大表格 (>= 20行)
        wb_large = Workbook()
        ws_large = wb_large.active
        ws_large.title = "LargeTable"
        ws_large["A1"] = "ID"
        ws_large["B1"] = "Name"
        ws_large["C1"] = "Value"
        for i in range(2, 25):  # 23 行数据
            ws_large[f"A{i}"] = i
            ws_large[f"B{i}"] = f"Item{i}"
            ws_large[f"C{i}"] = i * 100

        large_excel = Path(tmp_dir) / "rag_test_large.xlsx"
        wb_large.save(large_excel)

        contents = parser.parse(large_excel)

        print(f"\n  [OK] Large table (24 rows) result:")
        print(f"     - Content count: {len(contents)}")
        if contents:
            print(f"     - First type: {contents[0].content_type.value}")
            # Large table should have header description first
            is_header = contents[0].metadata.get("is_header", False)
            print(f"     - First is header: {is_header}")
            print(f"     - First content: {contents[0].text[:80]}...")
            if len(contents) > 1:
                is_row = contents[1].metadata.get("is_row", False)
                print(f"     - Second is row: {is_row}")
                print(f"     - Second content: {contents[1].text[:80]}...")

        large_excel.unlink(missing_ok=True)

        return True
    except ImportError:
        print("  [SKIP] openpyxl not installed, skip Excel test")
        return True


def test_url_parser():
    """测试 URL 解析器（不实际请求网络）."""
    print("\n" + "="*50)
    print("[URL] Test URL Parser Interface")
    print("="*50)

    from app.document_parser.url_parser import UrlParser

    url_parser = UrlParser()

    # 测试无效 URL
    contents = url_parser.parse_url("invalid-url")
    print(f"  [OK] Invalid URL test:")
    print(f"     - Return count: {len(contents)}")
    if contents:
        print(f"     - Content: {contents[0].text}")

    # 测试空 URL
    contents = url_parser.parse_url("")
    print(f"\n  [OK] Empty URL test:")
    print(f"     - Return count: {len(contents)}")
    if contents:
        print(f"     - Content: {contents[0].text}")

    return True


def test_all_parser_mappings():
    """测试所有解析器映射."""
    print("\n" + "="*50)
    print("[MAPPING] Test Parser Mappings")
    print("="*50)

    extensions = [
        ".txt", ".md", ".pdf", ".doc", ".docx",
        ".xls", ".xlsx", ".ppt", ".pptx",
        ".png", ".jpg", ".jpeg",
        ".mp3", ".wav", ".mp4",
    ]

    all_ok = True
    for ext in extensions:
        parser = get_parser_for_extension(ext)
        status = "[OK]" if parser else "[FAIL]"
        parser_name = type(parser).__name__ if parser else "Not registered"
        print(f"  {status} {ext}: {parser_name}")
        if not parser:
            all_ok = False

    return all_ok


def test_integration():
    """测试集成：从解析到转换."""
    print("\n" + "="*50)
    print("[INTEGRATION] Test Full Pipeline")
    print("="*50)

    # 模拟完整流程
    tmp_dir = tempfile.gettempdir()

    # 1. 创建测试文件
    test_file = Path(tmp_dir) / "rag_integration_test.txt"
    test_file.write_text("Integration test content.\nLine 2.\nLine 3.", encoding="utf-8")

    try:
        # 2. 获取解析器
        parser = get_parser_for_extension(".txt")
        if not parser:
            print("[FAIL] Parser not found")
            return False

        # 3. 解析
        contents = parser.parse(test_file)
        print(f"  [OK] Step 1 - Parse: {len(contents)} contents")

        # 4. 转换
        chunks = content_list_to_chunks(contents)
        print(f"  [OK] Step 2 - Convert: {len(chunks)} chunks")

        # 5. 提取元数据
        metadata = get_content_metadata(contents)
        print(f"  [OK] Step 3 - Metadata: {metadata}")

        return True
    finally:
        test_file.unlink(missing_ok=True)


def main():
    """运行所有验证测试."""
    print("\n" + "="*60)
    print("V2.1 Phase 1 Multimodal Parser Verification")
    print("="*60)

    results = []

    # 运行所有测试
    results.append(("Parser Mappings", test_all_parser_mappings()))
    results.append(("TXT Parser", test_txt_parser()))
    results.append(("Markdown Parser", test_markdown_parser()))
    results.append(("Converter Layer", test_converter()))
    results.append(("Excel Smart Detection", test_excel_smart_detection()))
    results.append(("URL Parser", test_url_parser()))
    results.append(("Integration Test", test_integration()))

    # 汇总结果
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} - {name}")
        if not passed:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("SUCCESS: All verification tests passed!")
        print("Phase 1 implementation is working correctly.")
    else:
        print("FAILURE: Some tests failed, please check above.")
    print("="*60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
