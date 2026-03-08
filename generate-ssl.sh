#!/bin/bash

# SSL 证书生成脚本
# 用于生成自签名证书（测试用）或准备 Let's Encrypt 证书

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="$SCRIPT_DIR/ssl"
DOMAIN="${DOMAIN:-localhost}"

echo "========================================="
echo "SSL 证书生成工具"
echo "========================================="
echo ""

# 创建证书目录
mkdir -p "$CERT_DIR"

# 选择证书类型
echo "请选择证书类型："
echo "1) 自签名证书（测试用，浏览器会警告）"
echo "2) 准备 Let's Encrypt 配置（推荐用于生产环境）"
read -p "请选择 [1-2]: " cert_type

case $cert_type in
    1)
        echo ""
        echo "生成自签名证书..."
        echo ""

        # 生成私钥
        openssl genrsa -out "$CERT_DIR/key.pem" 2048 2>/dev/null

        # 生成证书
        openssl req -new -x509 -key "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" -days 365 \
            -subj "/C=CN/ST=State/L=City/O=Organization/CN=$DOMAIN" 2>/dev/null

        # 设置权限
        chmod 600 "$CERT_DIR/key.pem"
        chmod 644 "$CERT_DIR/cert.pem"

        echo ""
        echo "✅ 自签名证书已生成！"
        echo "   证书位置: $CERT_DIR/cert.pem"
        echo "   私钥位置: $CERT_DIR/key.pem"
        echo ""
        echo "⚠️  警告：自签名证书会导致浏览器显示安全警告"
        echo "   这对于测试是正常的，生产环境应使用受信任的 CA 证书"
        ;;

    2)
        echo ""
        echo "准备 Let's Encrypt 证书配置..."
        echo ""

        # 创建 Let's Encrypt 配置
        cat > "$CERT_DIR/letsencrypt-setup.sh" << 'LE_EOF'
#!/bin/bash

# Let's Encrypt 证书申请脚本
# 使用 certbot 获取免费 SSL 证书

# 安装 certbot（如果未安装）
# apt-get install certbot -y

# 申请证书（使用 HTTP 验证）
certbot certonly --standalone \
    --email your-email@example.com \
    --agree-tos \
    --non-interactive \
    --domain yourdomain.com \
    --http-01-port 80

# 证书位置
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem

echo "证书申请完成！"
echo "证书位置：/etc/letsencrypt/live/yourdomain.com/"
LE_EOF

        chmod +x "$CERT_DIR/letsencrypt-setup.sh"

        echo ""
        echo "✅ Let's Encrypt 配置脚本已创建！"
        echo "   脚本位置: $CERT_DIR/letsencrypt-setup.sh"
        echo ""
        echo "📋 下一步："
        echo "   1. 编辑 $CERT_DIR/letsencrypt-setup.sh，修改域名和邮箱"
        echo "   2. 在服务器上运行该脚本申请证书"
        echo "   3. 更新 nginx-ssl.conf，使用 Let's Encrypt 证书路径"
        ;;

    *)
        echo "无效的选择"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "Docker Compose 配置"
echo "========================================="
echo ""

# 显示 Docker Compose 配置
cat << 'DOCKER_EOF'
# 在 docker-compose.yml 中添加以下配置：

services:
  spa:
    volumes:
      - ./frontend_spa/nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro
      # SSL 证书挂载（自签名证书）
      - ./frontend_spa/ssl:/etc/nginx/ssl:ro
      # 或者（Let's Encrypt 证书）
      # - /etc/letsencrypt:/etc/nginx/ssl:ro

    ports:
      - "443:443"  # HTTPS 端口
      - "80:80"     # HTTP 端口（重定向到 HTTPS）

# 或者使用域名映射：
# services:
#   spa:
#     ports:
#       - "yourdomain.com:443:443"
#       - "yourdomain.com:80:80"
DOCKER_EOF

echo ""
echo "========================================="
echo "CORS 配置更新"
echo "========================================="
echo ""

# 显示 CORS 配置建议
cat << 'CORS_EOF'
# 更新 .env 文件，添加 HTTPS 地址：

CORS_ORIGINS=http://localhost:3000,http://localhost:3003,https://yourdomain.com
CORS_EOF

echo ""
echo "========================================="
echo "完成！"
echo "========================================="
echo ""
echo "📋 检查清单："
echo "   [ ] SSL 证书已生成"
echo "   [ ] docker-compose.yml 已更新（端口和证书挂载）"
echo "   [ ] .env 已更新（HTTPS CORS）"
echo "   [ ] 防火墙已开放 443 端口"
echo "   [ ] 路由器已配置端口转发（443 -> 服务器）"
echo ""
