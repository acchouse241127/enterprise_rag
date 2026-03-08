# SPA 前端外网访问：Nginx + SSH 隧道

通过在一台**有公网 IP 的服务器（VPS）**上运行 Nginx，并在运行 SPA 的本机建立 **SSH 反向隧道**，实现从外网访问本机的**完整项目**（前端 + 后端 API + 登录与全部功能）。

## 一键启动完整项目（推荐）

在项目根目录执行：

```powershell
.\scripts\start-full-project.ps1
```

会依次：启动 Docker 完整栈（postgres、chromadb、redis、backend、spa、worker）→ 等待 SPA 就绪 → 若已配置 `.env.tunnel` 则自动建立外网隧道。仅启动不建隧道可加参数：`.\scripts\start-full-project.ps1 -NoTunnel`。

## 架构示意

```
外网用户 → VPS:80 (Nginx) → 127.0.0.1:10080 (SSH 隧道) → 本机:3000 (SPA 容器 → 后端 API)
```

- **本机**：Docker Compose 运行**完整项目**（postgres、chromadb、redis、backend、spa、worker）。SPA 对外端口默认 3000，并将 `/api`、`/health` 代理到后端，故外网访问到的即整站（登录、知识库、对话等均可使用）。
- **VPS**：安装 Nginx，监听 80，将请求反向代理到 `127.0.0.1:10080`。
- **SSH 反向隧道**：在本机执行，把 VPS 的 10080 端口转发到本机 3000 端口。

## 前置条件

- 本机已用 Docker Compose 启动 SPA（`docker compose --profile full up -d`），前端可通过 `http://localhost:3000` 访问。
- 有一台带公网 IP 的 Linux 服务器（VPS），已安装 Nginx 和 OpenSSH，且本机可通过 SSH 登录。

## 步骤一：本机启动 SPA

```bash
# 在项目根目录
docker compose --profile full up -d

# 确认前端可访问（默认端口 3000）
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
# 期望 200
```

若修改过端口，请记下实际端口（例如 `SPA_PORT=3080` 则端口为 3080），后面隧道用该端口。

## 步骤二：在 VPS 上配置 Nginx

1. 将项目中的公网 Nginx 配置复制到 VPS：

   ```bash
   # 在本机执行（或手动复制 frontend_spa/nginx-public-server.conf 内容）
   scp frontend_spa/nginx-public-server.conf user@你的VPS:/tmp/enterprise_rag_spa.conf
   ```

2. 在 VPS 上放置并启用配置：

   ```bash
   ssh user@你的VPS
   sudo mv /tmp/enterprise_rag_spa.conf /etc/nginx/conf.d/enterprise_rag_spa.conf
   # 如有域名，编辑该文件把 your-domain.com 改成你的域名
   sudo nginx -t && sudo systemctl reload nginx
   ```

3. 确保 VPS 防火墙放行 80（如需 HTTPS 再放行 443）。

## 步骤三：建立 SSH 反向隧道（本机执行）

在本机（运行 Docker 的那台机器）执行：

```bash
# 将 VPS 的 10080 端口转发到本机 3000（SPA 端口）
ssh -R 10080:localhost:3000 -N user@你的VPS
```

- `10080`：VPS 上 Nginx 里 `proxy_pass` 使用的端口，需与 `nginx-public-server.conf` 中一致。
- `3000`：本机 SPA 暴露的端口（与 `SPA_PORT` 一致）。
- `-N`：不执行远程命令，只做端口转发。保持该终端不关闭，隧道会一直存在。

如需后台运行且断开 SSH 后仍保持隧道，可使用：

```bash
ssh -f -R 10080:localhost:3000 -N -o ServerAliveInterval=60 user@你的VPS
```

若 VPS 的 `sshd` 默认不允许远程端口绑定到 127.0.0.1 以外的地址，当前配置已使用 127.0.0.1:10080，一般无需改 `GatewayPorts`。

## 步骤四：从外网访问

- 浏览器访问：`http://你的VPS公网IP` 或 `http://你的域名`。
- 若配置正确，会看到 SPA 前端页面，且 /api 请求会经 Nginx → 隧道 → 本机 SPA → 后端。

## 故障排查

| 现象 | 可能原因 | 处理 |
|------|----------|------|
| 外网访问 VPS:80 超时 | 防火墙未放行 80 | 在 VPS 放行 80（及 443） |
| 502 Bad Gateway | 隧道未建立或已断开 | 在本机重新执行 `ssh -R 10080:localhost:3000 -N user@VPS` |
| 502 Bad Gateway | 本机 SPA 未启动或端口不对 | 确认 `http://localhost:3000` 可访问，且隧道中的端口为 3000 |
| 隧道建立失败 | VPS sshd 禁止 TCP 转发 | 在 VPS 检查 `/etc/ssh/sshd_config` 中 `AllowTcpForwarding yes` |

## 可选：HTTPS（VPS 上 Nginx）

若在 VPS 上配置了 SSL 证书，可新增 443 server，将 `proxy_pass` 同样指向 `http://127.0.0.1:10080`，并确保隧道始终指向本机 SPA 端口（如 3000）。证书配置可参考 `frontend_spa/nginx-ssl.conf` 的思路，在 VPS 的 Nginx 里为 443 配置 `ssl_certificate` / `ssl_certificate_key`。

## 相关文件

- `frontend_spa/nginx.conf`：Docker 内 SPA 使用的 Nginx 配置（本机）。
- `frontend_spa/nginx-public-server.conf`：公网服务器（VPS）使用的 Nginx 配置。
- `frontend_spa/nginx-ssl.conf`：SPA 容器内 HTTPS 参考配置（可选）。
