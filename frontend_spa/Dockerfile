# 构建阶段
FROM docker.m.daocloud.io/library/node:20-alpine AS builder

WORKDIR /app

# 复制 package.json 并安装依赖
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# 生产阶段 - 使用 nginx 服务静态文件
FROM docker.m.daocloud.io/library/nginx:alpine

# 复制构建产物到 nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
