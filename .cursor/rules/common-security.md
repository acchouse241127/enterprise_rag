---
description: "Mandatory security checks, secret management, and security response protocol"
description_zh: "强制性安全检查、密钥管理及安全响应协议"
alwaysApply: true
---

# Security Guidelines / 安全指南

## Mandatory Security Checks / 强制性安全检查

Before ANY commit:
任何提交前：
- [ ] No hardcoded secrets (API keys, passwords, tokens)
   无硬编码密钥（API 密钥、密码、token）
- [ ] All user inputs validated
   所有用户输入已验证
- [ ] SQL injection prevention (parameterized queries)
   防 SQL 注入（参数化查询）
- [ ] XSS prevention (sanitized HTML)
   防 XSS（净化 HTML）
- [ ] CSRF protection enabled
   启用 CSRF 防护
- [ ] Authentication/authorization verified
   认证/授权已验证
- [ ] Rate limiting on all endpoints
   所有端点限流
- [ ] Error messages don't leak sensitive data
   错误信息不泄露敏感数据

## Secret Management / 密钥管理

- NEVER hardcode secrets in source code
  切勿在源码中硬编码密钥
- ALWAYS use environment variables or a secret manager
  始终使用环境变量或密钥管理器
- Validate that required secrets are present at startup
  启动时验证所需密钥存在
- Rotate any secrets that may have been exposed
  轮换可能已泄露的密钥

## Security Response Protocol / 安全响应协议

If security issue found:
若发现安全问题：
1. STOP immediately
   立即停止
2. Use **security-reviewer** agent
   使用 **security-reviewer** 代理
3. Fix CRITICAL issues before continuing
   修复 CRITICAL 问题后再继续
4. Rotate any exposed secrets
   轮换已泄露的密钥
5. Review entire codebase for similar issues
   审查整个代码库寻找类似问题
