#!/bin/bash

# 简化的 SSL 证书生成脚本

cd "$(dirname "$0")"

# 生成私钥
openssl genrsa -out key.pem 2048

# 生成证书（使用 localhost）
openssl req -new -x509 -key key.pem -out cert.pem -days 365 -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"

echo "SSL 证书生成完成！"
echo "私钥: key.pem"
echo "证书: cert.pem"
