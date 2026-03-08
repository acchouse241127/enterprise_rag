# 快速启动指南

## 当前状态

✅ HTTP 访问已配置
✅ SSL 证书已生成
✅ HTTPS 配置已准备
✅ CORS 配置已更新

## 访问方式

### 1️⃣ 局域网访问（同一 WiFi）

```
HTTP: http://192.168.50.205:3000
```

手机和电脑在**同一 WiFi**下直接访问即可。

### 2️⃣ HTTPS 本地访问（需要启用）

```bash
# 运行 HTTPS 启用脚本
cd "E:\Super Fund\enterprise_rag"
bash enable-https.sh
```

然后访问：
```
HTTPS: https://192.168.50.205:443
```

⚠️ **注意**：浏览器会显示证书警告，点击"继续访问"即可。

### 3️⃣ 公网访问（需要配置路由器）

#### 步骤 1：获取公网 IP

访问：https://ifconfig.me

#### 步骤 2：配置路由器端口转发

| 外部端口 | 内部 IP | 内部端口 | 协议 |
|---------|---------|---------|-------|
| 3000 | 192.168.50.205 | 80 | TCP |
| 443 | 192.168.50.205 | 443 | TCP |

#### 步骤 3：访问

```
HTTP: http://<公网IP>:3000
HTTPS: https://<公网IP>:443
```

### 4️⃣ 使用域名访问（推荐）

#### 步骤 1：配置域名 DNS

将域名 A 记录指向你的公网 IP。

#### 步骤 2：申请 Let's Encrypt 免费证书

```bash
# 在服务器上安装 certbot
sudo apt-get install certbot -y

# 申请证书
sudo certbot certonly --standalone \
    --email your-email@example.com \
    --agree-tos \
    --domain yourdomain.com \
    --http-01-port 80

# 证书位置
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

#### 步骤 3：更新配置

1. 更新 `frontend_spa/nginx.conf` 使用 Let's Encrypt 证书路径
2. 更新 `.env` 添加域名到 CORS：
   ```
   CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
   ```
3. 重启服务：
   ```bash
   cd "E:\Super Fund\enterprise_rag"
   docker-compose restart backend spa
   ```

#### 步骤 4：访问

```
https://yourdomain.com
```

## 登录凭证

```
用户名: admin
密码: admin123
```

## 故障排查

### 无法访问

1. **检查服务状态**
   ```bash
   cd "E:\Super Fund\enterprise_rag"
   docker-compose ps
   ```
   所有服务应显示 `Up`

2. **检查端口监听**
   ```bash
   docker-compose ps --format "table {{.Names}}\t{{.Ports}}"
   ```
   应看到：
   ```
   enterprise_rag_spa    0.0.0.0:3000->80/tcp
   enterprise_rag_backend    0.0.0.0:8000->8000/tcp
   ```

3. **检查防火墙**
   - Windows 防火墙允许端口 3000
   - 路由器防火墙允许端口 3000 和 443

### HTTPS 证书警告

自签名证书会导致浏览器警告，这是正常的。

生产环境应使用 Let's Encrypt 等受信任的 CA 签发的证书。

### CORS 错误

确保 `.env` 中的 `CORS_ORIGINS` 包含你访问的地址。

## 手机访问测试

### Android Chrome

1. 打开 Chrome 浏览器
2. 输入：`http://192.168.50.205:3000`
3. 使用 `admin` / `admin123` 登录

### iOS Safari

1. 打开 Safari 浏览器
2. 输入：`http://192.168.50.205:3000`
3. 使用 `admin` / `admin123` 登录

## 快速命令

### 启动 HTTPS
```bash
cd "E:\Super Fund\enterprise_rag"
bash enable-https.sh
```

### 禁用 HTTPS（恢复 HTTP）
```bash
# 编辑 frontend_spa/nginx.conf，注释 HTTPS server 块
docker-compose restart spa
```

### 查看服务状态
```bash
cd "E:\Super Fund\enterprise_rag"
docker-compose ps
```

### 重启所有服务
```bash
cd "E:\Super Fund\enterprise_rag"
docker-compose restart
```
