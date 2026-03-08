#!/bin/bash
echo "开始监听文件变化..."
# 监听 src 目录变化
while inotifywait -r -e modify,create,delete --format '%w%f' src 2>/dev/null || \
     fswatch -1 -r src 2>/dev/null || \
     chokidar-cli "src/**/*.tsx" "src/**/*.ts" 2>/dev/null; do
    echo "检测到文件变化，开始构建..."
    npm run build
    echo "构建完成，重启容器..."
    cd ..
    docker-compose restart spa
    cd frontend_spa
done
