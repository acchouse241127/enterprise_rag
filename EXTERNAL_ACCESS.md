# 外网访问项目指南

## 访问地址

### 方法 1：局域网访问（推荐）

如果你的手机和电脑在**同一个 WiFi 网络**，使用以下地址：

#### SPA (Docker 部署)
```
http://192.168.50.205:3000
```

#### Vite Dev (开发模式)
```
http://192.168.50.205:3003
```

#### 后端 API
```
http://192.168.50.205:8000
```

### 方法 2：公网访问（需要路由器配置）

如果需要从外部网络（如 4G/5G）访问：

#### 1. 路由器端口转发

登录路由器管理页面（通常是 `http://192.168.50.1` 或 `http://192.168.1.1`），配置端口转发：

| 服务 | 外部端口 | 内部 IP | 内部端口 |
|------|---------|---------|---------|
| SPA | 3000 | 192.168.50.205 | 3000 |
| 后端 | 8000 | 192.168.50.205 | 8000 |

#### 2. 获取公网 IP

访问以下网站查看你的公网 IP：
- https://ifconfig.me
- https://ipinfo.io

#### 3. 访问应用

使用公网 IP + 端口访问：

```
http://<你的公网IP>:3000
```

#### 4. 更新 CORS 配置

更新 `E:\Super Fund\enterprise_rag\.env` 文件：

```
CORS_ORIGINS=http://localhost:3000,http://localhost:3003,http://192.168.50.205:3000,http://<你的公网IP>:3000
```

然后重启服务：
```bash
cd "E:\Super Fund\enterprise_rag"
docker-compose restart backend spa
```

## 防火墙配置

### Windows 防火墙

1. 打开"控制面板" → "系统安全" → "Windows Defender 防火墙"
2. 点击"高级设置" → "入站规则"
3. 点击"新建规则"，添加以下端口：
   - **端口 3000** (TCP)
   - **端口 3003** (TCP)
   - **端口 8000** (TCP)
4. 操作选择"允许连接"

### 路由器防火墙

确保路由器允许以下端口：
- **TCP 3000** (SPA)
- **TCP 3003** (Vite Dev)
- **TCP 8000** (后端)

## 登录凭证

```
用户名: admin
密码: admin123
```

## 文件夹同步配置

### 容器内路径

```
/app/data/uploads/sync/{知识库ID}
```

例如：知识库 ID 为 84，则配置路径为：
```
/app/data/uploads/sync/84
```

### Windows 本地路径

将文件放到：
```
E:\Super Fund\enterprise_rag\data\uploads\sync\{知识库ID}
```

## 故障排查

### 问题：无法访问

**1. 检查服务状态**
```bash
cd "E:\Super Fund\enterprise_rag"
docker-compose ps
```

所有服务应该显示 `Up`。

**2. 检查端口监听**
```bash
docker-compose ps --format "table {{.Name}}\t{{.Ports}}"
```

应该看到：
```
enterprise_rag_spa    0.0.0.0:3000->80/tcp
enterprise_rag_backend    0.0.0.0:8000->8000/tcp
```

`0.0.0.0` 表示监听所有网络接口。

**3. 检查防火墙**
```bash
# Windows (PowerShell)
New-NetFirewallRule -DisplayName "Enterprise RAG" -Direction Inbound -LocalPort 3000,3003,8000 -Protocol TCP -Action Allow
```

**4. 测试局域网访问**
在电脑上用局域网 IP 访问：
```bash
curl http://192.168.50.205:3000
```

### 问题：CORS 错误

如果浏览器控制台显示 CORS 错误：

1. 确认 `.env` 文件中的 `CORS_ORIGINS` 包含你的访问地址
2. 重启服务

### 问题：登录失败

如果显示"网络错误"或"认证失败"：

1. 确认后端服务正在运行
2. 检查浏览器控制台的具体错误信息
3. 尝试清除浏览器缓存

## 手机访问示例

### Android

1. 确保手机连接到和电脑相同的 WiFi
2. 打开 Chrome 浏览器
3. 访问：`http://192.168.50.205:3000`
4. 使用凭证登录

### iOS

1. 确保手机连接到和电脑相同的 WiFi
2. 打开 Safari 浏览器
3. 访问：`http://192.168.50.205:3000`
4. 使用凭证登录

## 安全提醒

⚠️ **生产环境注意事项：**

1. **不要**将服务直接暴露到公网而不使用 VPN
2. 使用 HTTPS（需要配置 SSL 证书）
3. 修改默认密码
4. 配置 IP 白名单（如果需要）
5. 启用速率限制
