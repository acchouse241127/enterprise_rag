#!/usr/bin/env python3
"""
API 契约检查脚本

自动对比后端 Schema 定义与前端调用，发现不一致问题。

用法：
    python scripts/check_api_contract.py

Author: System Generated
Date: 2026-02-21
"""

import ast
import json
import re
from pathlib import Path
from typing import Any

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 后端 Schema 目录
BACKEND_SCHEMAS_DIR = PROJECT_ROOT / "backend" / "app" / "schemas"

# 前端目录（SPA）
SPA_DIR = PROJECT_ROOT / "frontend_spa" / "src"


def extract_schema_fields(schema_file: Path) -> dict[str, list[str]]:
    """从 Pydantic Schema 文件提取字段定义"""
    results = {}
    
    try:
        content = schema_file.read_text(encoding="utf-8")
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 查找继承自 BaseModel 的类
                for base in node.bases:
                    base_name = ""
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    if "BaseModel" in base_name or "Request" in node.name or "Data" in node.name:
                        fields = []
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                                field_name = item.target.id
                                if not field_name.startswith("_"):
                                    fields.append(field_name)
                        if fields:
                            results[node.name] = fields
    except Exception as e:
        print(f"解析 {schema_file} 失败: {e}")
    
    return results


def extract_spa_api_calls(file_path: Path) -> list[dict]:
    """从 SPA 文件提取 API 调用"""
    calls = []
    
    try:
        content = file_path.read_text(encoding="utf-8")
        
        # 查找 fetch/axios 调用
        url_patterns = [
            r'["\']([^"\']*/api/[^"\']*)["\']',
            r'`([^`]*/api/[^`]*)`',
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if not match.startswith("${"):  # 排除模板变量
                    calls.append({"file": str(file_path.name), "url": match})
        
        # 查找接口定义
        interface_pattern = r'interface\s+\w+\s*\{([^}]+)\}'
        interface_matches = re.findall(interface_pattern, content, re.DOTALL)
        for match in interface_matches:
            fields = re.findall(r'(\w+)\s*[?:]', match)
            if fields:
                calls.append({"file": str(file_path.name), "interface_fields": fields})
                
        # 查找 payload 构造
        payload_patterns = [
            r'const\s+\w+Payload\s*=\s*\{([^}]+)\}',
            r'body:\s*JSON\.stringify\(\{([^}]+)\}\)',
        ]
        for pattern in payload_patterns:
            payload_matches = re.findall(pattern, content, re.DOTALL)
            for match in payload_matches:
                fields = re.findall(r'(\w+):', match)
                if fields:
                    calls.append({"file": str(file_path.name), "payload_fields": fields})
                    
    except Exception as e:
        print(f"解析 {file_path} 失败: {e}")
    
    return calls


def check_qa_contract():
    """检查问答 API 契约"""
    print("\n=== 问答 API 契约检查 ===\n")

    # 后端定义
    qa_schema_file = BACKEND_SCHEMAS_DIR / "qa.py"
    if qa_schema_file.exists():
        schemas = extract_schema_fields(qa_schema_file)
        print("后端 QaAskRequest 字段:")
        request_fields = schemas.get("QaAskRequest", [])
        for field in request_fields:
            print(f"  - {field}")
    else:
        print("未找到 qa.py schema 文件")
        request_fields = []

    # 检查 SPA
    print("\nSPA 问答页字段使用:")
    spa_qa = SPA_DIR / "pages" / "QA.tsx"
    if spa_qa.exists():
        calls = extract_spa_api_calls(spa_qa)
        for call in calls:
            if "payload_fields" in call:
                print(f"  文件: {call['file']}")
                for field in call["payload_fields"]:
                    status = "✅" if field in request_fields else "❓"
                    print(f"    {status} {field}")

    # 对比分析
    print("\n--- 差异分析 ---")

    if request_fields:
        print("\n后端有但前端未传递的字段:")
        spa_used = set()

        if spa_qa.exists():
            calls = extract_spa_api_calls(spa_qa)
            for call in calls:
                if "payload_fields" in call:
                    spa_used.update(call["payload_fields"])

        for field in request_fields:
            in_spa = field in spa_used
            spa_status = "✅" if in_spa else "❌"
            print(f"  {field}: SPA {spa_status}")


def check_knowledge_base_contract():
    """检查知识库 API 契约"""
    print("\n=== 知识库 API 契约检查 ===\n")
    
    kb_schema_file = BACKEND_SCHEMAS_DIR / "knowledge_base.py"
    if kb_schema_file.exists():
        schemas = extract_schema_fields(kb_schema_file)
        print("后端 Schema 定义:")
        for name, fields in schemas.items():
            print(f"  {name}: {fields}")


def generate_report():
    """生成完整报告"""
    print("=" * 60)
    print("API 契约检查报告")
    print("=" * 60)
    
    check_qa_contract()
    check_knowledge_base_contract()
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)


if __name__ == "__main__":
    generate_report()
