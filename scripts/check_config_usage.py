#!/usr/bin/env python3
"""
配置项使用检查脚本

自动检查 config.py 中的配置项是否在代码中被实际使用。

用法：
    python scripts/check_config_usage.py

Author: System Generated
Date: 2026-02-21
"""

import ast
import re
from pathlib import Path
from typing import Any

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 后端目录
BACKEND_DIR = PROJECT_ROOT / "backend" / "app"

# 配置文件
CONFIG_FILE = BACKEND_DIR / "core" / "config.py"


def extract_config_items() -> dict[str, dict]:
    """从 config.py 提取所有配置项"""
    configs = {}
    
    try:
        content = CONFIG_FILE.read_text(encoding="utf-8")
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "Settings":
                for item in node.body:
                    # 查找带类型注解的属性
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        field_name = item.target.id
                        # 跳过私有属性和特殊属性
                        if not field_name.startswith("_") and field_name != "model_config":
                            # 获取默认值
                            default_value = None
                            if item.value:
                                if isinstance(item.value, ast.Constant):
                                    default_value = item.value.value
                                elif isinstance(item.value, ast.List):
                                    default_value = "[]"
                                elif isinstance(item.value, ast.Dict):
                                    default_value = "{}"
                                elif isinstance(item.value, ast.Name):
                                    default_value = item.value.id
                            
                            # 获取类型
                            type_hint = ""
                            if isinstance(item.annotation, ast.Name):
                                type_hint = item.annotation.id
                            elif isinstance(item.annotation, ast.Constant):
                                type_hint = item.annotation.value
                            elif isinstance(item.annotation, ast.Subscript):
                                if isinstance(item.annotation.value, ast.Name):
                                    type_hint = item.annotation.value.id + "[...]"
                            
                            configs[field_name] = {
                                "type": type_hint,
                                "default": default_value,
                                "usage_count": 0,
                                "usage_locations": [],
                            }
    except Exception as e:
        print(f"解析配置文件失败: {e}")
    
    return configs


def search_usage_in_file(file_path: Path, config_name: str) -> list[str]:
    """在文件中搜索配置项使用"""
    usages = []
    
    try:
        content = file_path.read_text(encoding="utf-8")
        
        # 搜索模式
        patterns = [
            rf"settings\.{config_name}",
            rf'getattr\(settings,\s*["\']?{config_name}["\']?',
            rf'os\.environ\.get\(["\']?{re.sub(r"_", ".", config_name.upper())}["\']?',
        ]
        
        for pattern in patterns:
            if re.search(pattern, content):
                usages.append(str(file_path.relative_to(PROJECT_ROOT)))
                break
    except Exception:
        pass
    
    return usages


def check_all_usages(configs: dict[str, dict]):
    """检查所有配置项的使用情况"""
    
    # 遍历后端目录
    for py_file in BACKEND_DIR.rglob("*.py"):
        if py_file.name == "config.py":
            continue  # 跳过配置文件本身
        
        for config_name in configs:
            usages = search_usage_in_file(py_file, config_name)
            if usages:
                configs[config_name]["usage_count"] += len(usages)
                configs[config_name]["usage_locations"].extend(usages)


def generate_report(configs: dict[str, dict]):
    """生成报告"""
    print("=" * 70)
    print("配置项使用检查报告")
    print("=" * 70)
    
    # 分类统计
    used_configs = {k: v for k, v in configs.items() if v["usage_count"] > 0}
    unused_configs = {k: v for k, v in configs.items() if v["usage_count"] == 0}
    
    print(f"\n配置项总数: {len(configs)}")
    print(f"已使用: {len(used_configs)}")
    print(f"未使用: {len(unused_configs)}")
    
    # 未使用的配置项
    if unused_configs:
        print("\n" + "-" * 70)
        print("未使用的配置项:")
        print("-" * 70)
        for name, info in unused_configs.items():
            print(f"  {name}")
            print(f"    类型: {info['type']}")
            print(f"    默认值: {info['default']}")
    
    # 使用次数较少的配置项
    low_usage = {k: v for k, v in used_configs.items() if v["usage_count"] <= 2}
    if low_usage:
        print("\n" + "-" * 70)
        print("使用次数较少的配置项 (<=2次):")
        print("-" * 70)
        for name, info in low_usage.items():
            print(f"  {name} ({info['usage_count']}次)")
            for loc in info["usage_locations"][:3]:
                print(f"    - {loc}")
    
    # 常用配置项
    high_usage = sorted(used_configs.items(), key=lambda x: x[1]["usage_count"], reverse=True)[:10]
    print("\n" + "-" * 70)
    print("最常用的配置项 TOP 10:")
    print("-" * 70)
    for name, info in high_usage:
        print(f"  {name}: {info['usage_count']}次")
    
    # 问题配置项
    print("\n" + "-" * 70)
    print("需关注的配置项:")
    print("-" * 70)
    
    # 检查特定问题
    problem_configs = [
        ("retrieval_query_expansion_mode", "LLM 模式可能未完全对接"),
        ("llm_task_overrides", "代码中存在但未实际使用"),
    ]
    
    for config_name, issue in problem_configs:
        if config_name in configs:
            info = configs[config_name]
            print(f"\n  {config_name}:")
            print(f"    问题: {issue}")
            print(f"    使用次数: {info['usage_count']}")
            if info['usage_locations']:
                print(f"    使用位置: {', '.join(info['usage_locations'][:3])}")
    
    print("\n" + "=" * 70)
    print("检查完成")
    print("=" * 70)


def main():
    """主函数"""
    print("正在分析配置文件...")
    configs = extract_config_items()
    
    print(f"找到 {len(configs)} 个配置项")
    print("正在检查使用情况...")
    
    check_all_usages(configs)
    generate_report(configs)


if __name__ == "__main__":
    main()
