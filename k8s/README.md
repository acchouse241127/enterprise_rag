# Kubernetes 部署指南

本指南介绍如何将 Enterprise RAG 系统部署到 Kubernetes 集群。

## 前置要求

- Kubernetes 集群（v1.20+）
- kubectl 命令行工具
- Docker 镜像仓库访问权限
- DNS 域名（用于 Ingress）

## 快速部署

### 1. 配置参数

编辑 `k8s/config.yaml` 文件，设置你的环境参数：

```yaml
postgres-password: "your-secure-password"  # 数据库密码
jwt-secret-key: "your-32-char-random-secret"  # JWT 密钥
llm-api-key: "your-llm-api-key"  # LLM API 密钥
cors-origins: "https://your-domain.com"  # CORS 白名单
```

### 2. 创建 Secret

```bash
kubectl create secret generic enterprise-rag-secrets \
  --from-literal=postgres-password='your-secure-password' \
  --from-literal=jwt-secret-key='your-32-char-random-secret' \
  --from-literal=llm-api-key='your-llm-api-key'
```

### 3. 部署后端

```bash
kubectl apply -f k8s/backend-deployment.yaml
```

### 4. 部署前端

```bash
kubectl apply -f k8s/spa-deployment.yaml
```

### 5. 配置 Ingress

编辑 `k8s/ingress.yaml`，替换 `your-domain.com` 为你的实际域名：

```yaml
spec:
  tls:
  - hosts:
    - rag.example.com
    secretName: enterprise-rag-tls
  rules:
  - host: rag.example.com
```

应用 Ingress 配置：

```bash
kubectl apply -f k8s/ingress.yaml
```

## 验证部署

### 检查 Pod 状态

```bash
kubectl get pods -l app=enterprise-rag-backend
kubectl get pods -l app=enterprise-rag-spa
```

预期输出：
```
NAME                                  READY   STATUS    RESTARTS   AGE
enterprise-rag-backend-xxxxxxxxxx-xxxx   1/1     Running   0          5m
enterprise-rag-spa-xxxxxxxxxx-xxxx        1/1     Running   0          5m
```

### 检查服务状态

```bash
kubectl get svc
```

### 访问应用

- **后端 API**：http://your-backend-ip:8000
- **前端界面**：https://rag.example.com

## 扩展应用

### 水平扩展后端

```bash
kubectl scale deployment enterprise-rag-backend --replicas=3
```

### 水平扩展前端

```bash
kubectl scale deployment enterprise-rag-spa --replicas=3
```

## 监控和日志

### 查看日志

```bash
# 后端日志
kubectl logs -l app=enterprise-rag-backend --tail=100 -f

# 前端日志
kubectl logs -l app=enterprise-rag-spa --tail=100 -f
```

### 查看指标

后端暴露了 Prometheus 指标端点：

```bash
kubectl port-forward svc/enterprise-rag-backend 8000:8000
curl http://localhost:8000/metrics
```

## 故障排查

### Pod 启动失败

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### 健康检查失败

检查健康检查端点是否正确：

```bash
kubectl exec -it <pod-name> -- curl http://localhost:8000/health
```

### 存储问题

检查 PVC 状态：

```bash
kubectl get pvc
kubectl describe pvc enterprise-rag-uploads-pvc
```

## 清理

删除所有 K8s 资源：

```bash
kubectl delete -f k8s/
kubectl delete secret enterprise-rag-secrets
kubectl delete pvc enterprise-rag-uploads-pvc
```

## 安全建议

1. **使用 Secret 管理敏感信息**：不要将密码提交到代码仓库
2. **启用 RBAC**：为不同用户分配适当的权限
3. **配置网络策略**：限制 Pod 之间的网络访问
4. **启用 Pod 安全策略**：限制容器权限
5. **定期更新镜像**：使用最新版本修复安全漏洞
