#!/bin/bash

# HTTPS 启用脚本
# 快速启用 HTTPS 配置（使用自签名证书）

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NGINX_CONF="$PROJECT_DIR/frontend_spa/nginx.conf"
SSL_DIR="$PROJECT_DIR/frontend_spa/ssl"

echo "========================================="
echo "HTTPS 启用工具"
echo "========================================="
echo ""

# 检查证书
if [ ! -f "$SSL_DIR/cert.pem" ] || [ ! -f "$SSL_DIR/key.pem" ]; then
    echo "❌ SSL 证书不存在！"
    echo "请先运行以下命令生成证书："
    echo ""
    echo "cd $SSL_DIR"
    echo "openssl genrsa -out key.pem 2048"
    echo "openssl req -new -x509 -key key.pem -out cert.pem -days 365 -subj \"/C=CN/ST=State/L=City/O=Organization/CN=localhost\""
    echo ""
    exit 1
fi

echo "✅ SSL 证书检查通过"
echo ""

# 取消注释 HTTPS 配置
echo "正在启用 HTTPS 配置..."
cat > "$NGINX_CONF" << 'NGINX_EOF'
# HTTP 服务器 - 重定向到 HTTPS
server {
    listen 80;
    server_name _;

    # 将所有 HTTP 请求重定向到 HTTPS
    return 301 https://\$host\$request_uri;
}

# HTTPS 服务器
server {
    listen 443 ssl http2;
    server_name _;

    # SSL 证书配置
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    root /usr/share/nginx/html;
    index index.html;

    # 上传文件大小限制
    client_max_body_size 200M;

    # API 代理到后端
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;

        # SSE 支持
        proxy_buffering off;
        proxy_read_timeout 86400;
    }

    # 健康检查代理
    location /health {
        proxy_pass http://backend:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA 路由 - 所有路径返回 index.html
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    gzip_min_length 1000;
}
NGINX_EOF

echo "✅ HTTPS 配置已启用！"
echo ""

# 重启服务
echo "正在重启服务..."
cd "$PROJECT_DIR"
docker-compose restart spa

echo ""
echo "========================================="
echo "完成！"
echo "========================================="
echo ""
echo "📱 访问地址："
echo ""
echo "HTTP（自动重定向到 HTTPS）："
echo "  http://192.168.50.205:3000"
echo ""
echo "HTTPS："
echo "  https://192.168.50.205:443"
echo ""
echo "⚠️  浏览器可能会显示证书警告，这是正常的（自签名证书）"
echo ""
echo "📋 公网访问（需要配置路由器端口转发）："
echo "  http://<你的公网IP>:3000"
echo "  https://<你的公网IP>:443"
echo ""
