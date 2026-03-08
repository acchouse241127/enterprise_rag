# SSL HTTPS 外网访问配置指南

## 📋 前置条件

1. ✅ SSL 证书已生成（位于 `frontend_spa/ssl/`）
2. ✅ docker-compose.yml 已更新（添加 443 端口和证书挂载）
3. ✅ CORS 配置已更新（支持 HTTPS）
4. ✅ nginx.conf 已更新（支持 HTTP 到 HTTPS 重定向）

## 🔧 启用 HTTPS

### 方式 1：自签名证书（测试用）

当前已生成自签名证书，可以直接使用：

1. 取消注释 nginx.conf 中的 HTTPS 服务器配置
2. 重启服务

```bash
cd "E:\Super Fund\enterprise_rag"
docker-compose restart spa
```

3. 访问：`https://192.168.50.205:443`

⚠️ **注意**：浏览器会显示"不安全"警告，这是正常的（因为证书是自签名的）

### 方式 2：Let's Encrypt 免费证书（推荐用于生产）

#### 1. 准备域名

确保你有以下条件：
- 一个域名（如 `yourdomain.com`）
- 域名 DNS 已解析到你的公网 IP
- 防火墙开放 80 和 443 端口

#### 2. 申请证书

在服务器上运行 certbot：

```bash
# 安装 certbot（如果未安装）
sudo apt-get update
sudo apt-get install certbot -y

# 申请证书（使用 HTTP 验证）
sudo certbot certonly --standalone \
    --email your-email@example.com \
    --agree-tos \
    --non-interactive \
    --domain yourdomain.com \
    --http-01-port 80

# 或申请通配符证书
sudo certbot certonly --standalone \
    --email your-email@example.com \
    --agree-tos \
    --non-interactive \
    --domain *.yourdomain.com \
    --http-01-port 80
```

证书将安装在：
- `/etc/letsencrypt/live/yourdomain.com/fullchain.pem`
- `/etc/letsencrypt/live/yourdomain.com/privkey.pem`

#### 3. 更新 nginx.conf

取消注释 HTTPS 服务器配置，并更新证书路径：

```nginx
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
```

#### 4. 更新 docker-compose.yml

```yaml
services:
  spa:
    volumes:
      - /etc/letsencrypt:/etc/nginx/ssl:ro  # 替换自签名证书挂载
```

#### 5. 自动续期

Let's Encrypt 证书有效期为 90 天，需要定期续期：

```bash
# 手动续期
sudo certbot renew

# 或设置自动续期
sudo certbot renew --dry-run
echo "0 0 1 * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

## 📱 手机外网访问配置

### 1. 获取公网 IP

访问以下网站查看你的公网 IP：
- https://ifconfig.me
- https://ipinfo.io
- https://checkip.amazonaws.com

### 2. 配置路由器

登录路由器管理页面，配置端口转发：

| 外部端口 | 内部 IP | 内部端口 | 协议 |
|---------|---------|---------|-------|
| 80 | 192.168.50.205 | 80 | TCP |
| 443 | 192.168.50.205 | 443 | TCP |

### 3. 更新 CORS 配置

更新 `.env` 文件，添加公网域名/IP：

```bash
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

重启服务：
```bash
cd "E:\Super Fund\enterprise_rag"
docker-compose restart backend spa
```

### 4. 手机访问

#### 局域网（手机和电脑在同一 WiFi）
```
http://192.168.50.205:3000  # HTTP
https://192.168.50.205:443 # HTTPS
```

#### 公网访问（手机使用 4G/5G）
```
http://<公网IP>:3000  # HTTP
https://<公网IP>:443 # HTTPS
```

或使用域名：
```
https://yourdomain.com
```

## 🛡️ 安全配置

### 1. 修改默认密码

```bash
# 在容器中运行
docker exec enterprise_rag_backend python -c "
import sys
sys.path.insert(0, '/app')
from app.core.security import hash_password
from app.models.user import User
from app.core.database import SessionLocal

db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
admin.password_hash = hash_password('你的新密码')
db.commit()
db.close()
print('密码已更新')
"
```

### 2. 启用速率限制

已在 `.env` 中配置：
```bash
# 速率限制（防 DDoS）
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=200
```

### 3. 启用 HTTPS 强制重定向

取消注释 nginx.conf 中的重定向配置：
```nginx
return 301 https://$host$request_uri;
```

## 🔍 故障排查

### 问题 1：无法访问 HTTPS

**检查清单：**
- [ ] SSL 证书存在（`frontend_spa/ssl/cert.pem`）
- [ ] 证书挂载到容器
- [ ] 443 端口已开放（防火墙和路由器）
- [ ] nginx.conf HTTPS 配置已取消注释

**测试命令：**
```bash
# 检查 443 端口是否监听
docker exec enterprise_rag_spa netstat -tlnp | grep :443

# 测试 HTTPS 连接
curl -k https://localhost:443  # -k 忽略证书验证
```

### 问题 2：CORS 错误

**症状：** 浏览器控制台显示 CORS 错误

**解决方案：**
1. 检查 `.env` 中的 `CORS_ORIGINS` 是否包含访问的地址
2. 重启后端服务
3. 清除浏览器缓存

### 问题 3：证书验证失败

**症状：** 浏览器无法验证证书

**解决方案：**
1. 使用 `curl -k` 跳过证书验证测试
2. 检查证书和私钥是否匹配
3. 检查域名 DNS 是否正确解析

### 问题 4：端口被占用

**症状：** 启动失败，端口已被占用

**解决方案：**
```bash
# Windows
netstat -ano | findstr :443

# 或使用其他端口
# 更新 docker-compose.yml：443 -> 8443
```

## 📝️ 快速启动命令

### 使用自签名证书快速启动

```bash
cd "E:\Super Fund\enterprise_rag"

# 1. 确保 nginx.conf HTTPS 配置已取消注释
# 编辑 frontend_spa/nginx.conf

# 2. 重启服务
docker-compose restart backend spa

# 3. 验证
docker exec enterprise_rag_spa nginx -t

# 4. 测试访问
curl -k https://localhost:443
```

### 使用 Let's Encrypt 证书完整流程

```bash
# 1. 申请证书
sudo certbot certonly --standalone --domain yourdomain.com

# 2. 拷贝证书到项目目录
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem E:/Super\ Fund/enterprise_rag/frontend_spa/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem E:/Super\ Fund/enterprise_rag/frontend_spa/ssl/key.pem

# 3. 更新 docker-compose.yml，使用 Let's Encrypt 路径
# 将挂载从 ./frontend_spa/ssl 改为 /etc/letsencrypt

# 4. 重启服务
cd "E:\Super Fund\enterprise_rag"
docker-compose restart backend spa
```

## 📚️ 参考资料

- [Let's Encrypt 官方文档](https://letsencrypt.org/docs/)
- [Nginx SSL 配置指南](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Docker Compose 文档](https://docs.docker.com/compose/)
