"""Excel parser implementation."""

from pathlib import Path

from .base import BaseDocumentParser


class ExcelDocumentParser(BaseDocumentParser):
    """Parser for Excel documents."""

    def parse(self, file_path: Path) -> str:
        from openpyxl import load_workbook  # type: ignore

        wb = load_workbook(filename=str(file_path), data_only=True)
        chunks: list[str] = []
        
        for sheet in wb.worksheets:
            chunks.append(f"[工作表: {sheet.title}]")
            
            # 获取所有行数据
            rows_data = list(sheet.iter_rows(values_only=True))
            if not rows_data:
                continue
            
            # 尝试识别表头（第一行非空行）
            header_row = None
            header_idx = 0
            for idx, row in enumerate(rows_data):
                values = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
                if values:
                    header_row = row
                    header_idx = idx
                    break
            
            if header_row is None:
                continue
            
            # 获取列名
            headers = []
            for cell in header_row:
                if cell is not None and str(cell).strip():
                    headers.append(str(cell).strip())
                else:
                    headers.append("")
            
            # 处理数据行，生成结构化描述
            for row_idx, row in enumerate(rows_data[header_idx + 1:], start=header_idx + 2):
                values = [cell for cell in row]
                # 检查是否有有效数据
                non_empty = [v for v in values if v is not None and str(v).strip()]
                if not non_empty:
                    continue
                
                # 生成键值对描述格式，更适合语义检索
                row_desc_parts = []
                for col_idx, value in enumerate(values):
                    if value is None or not str(value).strip():
                        continue
                    col_name = headers[col_idx] if col_idx < len(headers) and headers[col_idx] else f"列{col_idx+1}"
                    row_desc_parts.append(f"{col_name}: {str(value).strip()}")
                
                if row_desc_parts:
                    # 限制每行描述长度，避免过长
                    row_desc = " | ".join(row_desc_parts)
                    chunks.append(row_desc)
        
        return "\n".join(chunks)

