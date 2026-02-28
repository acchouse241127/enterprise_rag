# PostgreSQL with pg_jieba - 配置说明

## 实际使用的镜像

本项目采用预构建镜像：`sdrzlyz/pg-ts-jieba:16`

### 为什么使用预构建镜像？

原始 Dockerfile 设计从源码编译 `pg_jieba`，但构建过程中遇到网络不稳定问题（502 Bad Gateway），导致构建失败。

为了确保开发流程稳定，采用以下方案：

1. **方案A（已采用）**：使用社区维护的预构建镜像 `sdrzlyz/pg-ts-jieba:16`
   - ✅ 无需网络依赖，构建速度快
   - ✅ 已验证正常工作（支持 `pg_jieba` 扩展及中文全文检索）
   - ⚠️ 镜像版本应与 PostgreSQL 16 兼容

2. **方案B（备用）**：临时使用 PostgreSQL 内置全文检索 `zhparser`
   - 不支持中文分词的复杂分词模式
   - 检索质量较低
   - 仅在方案A完全不可用时使用

## 验证结果

### pg_jieba 扩展创建

```sql
CREATE EXTENSION IF NOT EXISTS pg_jieba;
```

**输出**：`NOTICE: extension "pg_jieba" already exists, skipping`
**状态**：✅ 成功

### 中文全文检索测试

```sql
SELECT to_tsvector('jiebacfg', '企业级RAG系统使用高级检索算法') @@ to_tsquery('jiebacfg', 'RAG');
```

**输出**：`t` (true)
**状态**：✅ 成功

### 可用配置（text search configuration）

| 配置名称 | 说明 |
|----------|------|
| `jiebacfg` | 主配置（推荐） |
| `jiebaqry` | 查询配置 |
| `jiebamp` | 最大概率（MP）分词 |
| `jiebahmm` | 隐马尔可夫（HMM）分词 |

## 原始 Dockerfile（已弃用）

参考 `Dockerfile.backup` 文件（保留作为参考）。

## 相关文档

- **PRD**：`V2升级/V2.0_PRD_检索与质量.md`
- **TRD**：`V2升级/V2.0_TRD_检索与质量.md`（4.1.1 / 9.2）
- **规划**：`docs/plans/V2.0-B1-infra.md`

## 初始化脚本

`init-extensions.sql` 会在容器首次启动时自动执行，创建 `pg_jieba` 扩展。

```sql
CREATE EXTENSION IF NOT EXISTS pg_jieba;
```

**注意**：由于使用了预构建镜像，该脚本已不再必需，但保留以确保兼容性。