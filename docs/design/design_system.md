# Enterprise RAG System - 设计规范 (Design System)

## 文档信息

| 项目 | 内容 |
|------|------|
| 角色 | R4 (UI/UX 设计师) |
| 任务 | R4-2.3.1 |
| 版本 | v1.0 |
| 日期 | 2026-02-13 |

---

## 1. 概述

本设计规范旨在统一 Enterprise RAG System 的视觉风格和交互体验。由于项目基于 Streamlit 框架，本规范充分考虑了 Streamlit 的组件能力和限制，提供可直接落地的设计指导。

---

## 2. 颜色规范 (Color Palette)

### 2.1 主色调 (Brand Colors)

| 颜色名称 | 色值 (Hex) | 用途 | Streamlit 对应 |
|----------|------------|------|----------------|
| **Primary Blue** | `#1E88E5` | 主要按钮、链接、激活状态 | `theme.primaryColor` |
| **Secondary Grey** | `#424242` | 次要信息、非激活状态 | - |

### 2.2 功能色 (Functional Colors)

| 颜色名称 | 色值 (Hex) | 用途 | Streamlit 组件 |
|----------|------------|------|----------------|
| **Success** | `#4CAF50` | 成功提示、完成状态 | `st.success` |
| **Warning** | `#FF9800` | 警告提示、注意状态 | `st.warning` |
| **Error** | `#F44336` | 错误提示、危险操作 | `st.error` |
| **Info** | `#2196F3` | 信息提示、帮助说明 | `st.info` |

### 2.3 背景色 (Background Colors)

| 颜色名称 | 色值 (Hex) | 用途 | Streamlit 对应 |
|----------|------------|------|----------------|
| **Background** | `#FFFFFF` | 页面主背景 | `theme.backgroundColor` |
| **Surface** | `#F5F5F5` | 侧边栏、卡片背景 | `theme.secondaryBackgroundColor` |

### 2.4 文字色 (Text Colors)

| 颜色名称 | 色值 (Hex) | 用途 | Streamlit 对应 |
|----------|------------|------|----------------|
| **Text Primary** | `#212121` | 标题、正文 | `theme.textColor` |
| **Text Secondary** | `#757575` | 辅助说明、占位符 | - |
| **Text Disabled** | `#BDBDBD` | 禁用状态文字 | - |

---

## 3. 字体规范 (Typography)

Streamlit 默认使用系统字体栈 (Sans-serif)，本规范主要定义字号层级。

| 层级 | 字号 (rem/px) | 粗细 | 用途 | 对应 Markdown |
|------|---------------|------|------|---------------|
| **H1** | 2.0rem / 32px | Bold | 页面主标题 | `# Title` |
| **H2** | 1.5rem / 24px | Bold | 模块/区块标题 | `## Section` |
| **H3** | 1.25rem / 20px | Semi-Bold | 小节标题 | `### Subsection` |
| **Body** | 1.0rem / 16px | Regular | 正文内容 | Normal text |
| **Small** | 0.875rem / 14px | Regular | 辅助说明、脚注 | `<small>` or `st.caption` |

---

## 4. 间距规范 (Spacing)

统一使用 `rem` 单位，基准 `1rem = 16px`。

| 规格 | 尺寸 (rem) | 像素 (px) | 用途 |
|------|------------|-----------|------|
| **XS** | 0.25rem | 4px | 紧凑元素间距 |
| **SM** | 0.5rem | 8px | 图标与文字间距 |
| **MD** | 1.0rem | 16px | 组件间距、段落间距 |
| **LG** | 1.5rem | 24px | 区块间距 |
| **XL** | 2.0rem | 32px | 页面边缘、大模块间距 |

---

## 5. 组件交互规范 (Component Interaction)

### 5.1 按钮 (Buttons)

- **主要操作** (Primary Action): 使用 `st.button(..., type="primary")`。每个页面原则上只有一个主要操作按钮（如“登录”、“发送”、“上传”）。
- **次要操作** (Secondary Action): 使用默认 `st.button(...)`。
- **危险操作** (Danger Action): 涉及删除、重置等操作，需配合 `st.warning` 或二次确认逻辑（如 `if st.button("删除"): ...` 后跟确认）。

### 5.2 表单 (Forms)

- **批量提交**: 尽量使用 `st.form` 包裹输入项，避免每填一项就刷新页面。
- **必填标记**: 必填项 Label 后加 `*`，如 `用户名 *`。
- **输入反馈**: 提交后需给出明确的 `st.success` 或 `st.error` 反馈。

### 5.3 表格 (Data Display)

- **数据展示**: 优先使用 `st.dataframe`，开启 `use_container_width=True` 以自适应宽度。
- **操作列**: 若需在表格行内操作，考虑使用 `st.data_editor` (Streamlit > 1.23) 或在表格下方/侧边提供操作区。

### 5.4 反馈与加载 (Feedback & Loading)

- **加载中**: 所有耗时操作（API 请求、文件处理）必须使用 `with st.spinner("正在..."):` 包裹。
- **成功**: 操作完成后使用 `st.success("操作成功")`，可设置 `icon="✅"`。
- **错误**: 遇到异常使用 `st.error("错误信息")`，可设置 `icon="🚨"`。
- **空状态**: 列表为空时，使用 `st.info("暂无数据")` 或 `st.caption` 提示。

---

## 6. 布局规范 (Layout)

### 6.1 页面结构

- **侧边栏 (`st.sidebar`)**: 放置全局导航、用户信息、全局设置（如知识库选择）。
- **主内容区**:
    - **顶部**: 页面标题 (`H1`)、面包屑（如有）。
    - **中部**: 核心功能区。
    - **底部**: 辅助信息或版权声明（可选）。

### 6.2 响应式

- 使用 `st.columns` 进行多列布局时，注意在移动端会自动堆叠。
- 避免在 `st.columns` 中嵌套过深。

---

## 7. 图标规范 (Icons)

- 优先使用 Emoji 作为图标（Streamlit 原生支持好）。
- **导航**: 🏠 首页, 💬 对话, 📚 知识库, 📄 文档, ⚙️ 设置
- **操作**: ➕ 新建, 🗑️ 删除, ✏️ 编辑, 📤 上传, 🔍 搜索
- **状态**: ✅ 成功, ❌ 失败, ⚠️ 警告, 🔄 处理中

