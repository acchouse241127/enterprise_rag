#!/usr/bin/env python3
"""
修复 LLM Query Expansion 对接问题

此脚本会自动修改 qa_service.py，添加 LLM provider 参数传递。

Author: System Generated
Date: 2026-02-21
"""

import re
from pathlib import Path

# 文件路径
QA_SERVICE_FILE = Path(__file__).resolve().parent.parent / "backend" / "app" / "services" / "qa_service.py"


def fix_llm_query_expansion():
    """修复 LLM Query Expansion 对接"""
    
    content = QA_SERVICE_FILE.read_text(encoding="utf-8")
    
    # 原始代码模式 (ask 方法)
    old_pattern_ask = r'''(        retrieval_start = time\.perf_counter\(\)
        queries = \[question\]
        if use_expansion:
            expansion_mode = getattr\(settings, "retrieval_query_expansion_mode", "rule"\)
            queries = expand_query\(question, mode=expansion_mode, max_extra=2\) or \[question\])'''
    
    # 新代码 (ask 方法)
    new_code_ask = '''        retrieval_start = time.perf_counter()
        queries = [question]
        if use_expansion:
            expansion_mode = getattr(settings, "retrieval_query_expansion_mode", "rule")
            # D4.1: 修复 LLM Query Expansion 对接
            expansion_llm = None
            if expansion_mode in ("llm", "hybrid"):
                try:
                    expansion_llm = get_provider_for_task("qa")
                except Exception as e:
                    logger.warning("LLM provider not available for query expansion: %s", e)
            queries = expand_query(
                question,
                mode=expansion_mode,
                llm_provider=expansion_llm,
                max_extra=2
            ) or [question]'''
    
    # 执行替换
    new_content = re.sub(old_pattern_ask, new_code_ask, content, count=1)
    
    if new_content != content:
        # 备份原文件
        backup_file = QA_SERVICE_FILE.with_suffix(".py.bak")
        backup_file.write_text(content, encoding="utf-8")
        
        # 写入新内容
        QA_SERVICE_FILE.write_text(new_content, encoding="utf-8")
        
        print(f"已修复 LLM Query Expansion 对接")
        print(f"备份文件: {backup_file}")
        return True
    else:
        print("未找到需要修复的代码模式，可能已经修复过了")
        return False


def verify_fix():
    """验证修复是否成功"""
    content = QA_SERVICE_FILE.read_text(encoding="utf-8")
    
    if "llm_provider=expansion_llm" in content:
        print("验证通过: LLM Query Expansion 对接代码已添加")
        return True
    else:
        print("验证失败: 未找到修复代码")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("修复 LLM Query Expansion 对接")
    print("=" * 60)
    
    if fix_llm_query_expansion():
        verify_fix()
    
    print("=" * 60)
    print("完成")
    print("=" * 60)
