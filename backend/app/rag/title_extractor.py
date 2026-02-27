"""Title extractor for document section titles.

Author: C2
Date: 2026-02-27
"""

import re
from dataclasses import dataclass

from typing import List


@dataclass
class TitleInfo:
    """标题信息"""
    title: str
    pos: int  # 在全文中的位置
    level: int  # 标题级别（1=一级标题，2=二级，...）


class TitleExtractor:
    """从文档文本中提取章节标题。

    支持格式：
    - Markdown：#, ##, ###
    - 中文章节：一、1.、（1）等
    """

    MD_HEADERS: List[str] = [
        r"^#{1}\s*(.+?)\s*$",   # H1: # 标题
        r"^#{2}\s*(.+?)\s*$",   # H2: ## 标题
        r"^#{3}\s*(.+?)\s*$",   # H3: ### 标题
    ]

    CN_HEADERS: List[str] = [
        r"^第[一二三四五六七八九十零]+章[、]\s*(.+?)$",   # 第X章 标题
        r"^[一二三四五六七八九十零]+[、]\s*(.+?)$",       # 一、标题
        r"^\d+[、]\s*(.+?)$",                           # 1、标题
        r"^\([一二三四五六七八九十零]+\)\s*(.+?)$",      # （一）标题
        r"^\([0123456789]+\)\s*(.+?)$",                 # (1) 标题
    ]

    def extract_titles(self, text: str) -> List[TitleInfo]:
        """提取文档中的所有标题。"""
        titles: List[TitleInfo] = []
        lines = text.split('\n')

        for line_num, line in enumerate(lines):
            title, level = self._match_title(line)
            if not title:
                continue
            pos = sum(len(l) + 1 for l in lines[:line_num])
            titles.append(TitleInfo(title=title, pos=pos, level=level))

        return titles

    def _match_title(self, line: str) -> tuple[str, int]:
        """匹配行是否为标题，返回 (标题, 级别)。"""
        stripped = line.strip()
        if not stripped:
            return "", 0

        for idx, pattern in enumerate(self.MD_HEADERS):
            m = re.match(pattern, stripped)
            if m:
                return m.group(1).strip(), idx + 1

        for idx, pattern in enumerate(self.CN_HEADERS):
            m = re.match(pattern, stripped)
            if m:
                return m.group(1).strip(), idx + 1 + 3

        return "", 0

    def assign_titles_to_chunks(
        self,
        chunks: List[str],
        titles: List[TitleInfo],
        text: str,
    ) -> List[str]:
        """为每个 chunk 分配最近的上方标题。"""
        if not titles:
            return [""] * len(chunks)

        chunk_positions: List[int] = []
        current_pos = 0
        for chunk in chunks:
            idx = text.find(chunk, current_pos)
            if idx != -1:
                chunk_positions.append(idx)
                current_pos = idx + len(chunk)
            else:
                chunk_positions.append(current_pos)

        section_titles: List[str] = []
        for pos in chunk_positions:
            prev_title = None
            for title in reversed(titles):
                if title.pos <= pos:
                    prev_title = title
                    break
            section_titles.append(prev_title.title if prev_title else "")

        return section_titles