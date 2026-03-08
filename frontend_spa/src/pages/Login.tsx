import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "@/api/auth";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";

export default function Login() {
  const navigate = useNavigate();
  const { login: setAuth } = useAuthStore();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const verifyGateway = async () => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 8000);
    try {
      const res = await fetch("/health", {
        method: "GET",
        cache: "no-store",
        signal: controller.signal,
      });
      if (!res.ok) {
        throw new Error(`健康检查失败(${res.status})`);
      }
    } finally {
      window.clearTimeout(timer);
    }
  };

  const formatLoginError = (e: unknown) => {
    const err = e as {
      message?: string;
      code?: string;
      response?: { status?: number; data?: { detail?: string; message?: string } };
    };
    const detail = err.response?.data?.detail ?? err.response?.data?.message;
    if (detail) return detail;
    const origin = window.location.origin;
    const message = err.message ?? "未知错误";
    if (!err.response) {
      return `网络连接失败，请检查外网地址是否最新。站点：${origin}；接口：/api/auth/login；错误：${message}`;
    }
    return `登录失败(${err.response.status ?? "unknown"})：${message}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("请输入用户名和密码");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await verifyGateway();
      const res = await login(username.trim(), password);
      if (res.code !== 0) {
        setError(res.detail ?? res.message ?? "登录失败");
        return;
      }
      const token = res.data?.access_token;
      if (!token) {
        setError("登录失败：未返回令牌");
        return;
      }
      setAuth(token, username.trim());
      navigate("/");
    } catch (e: unknown) {
      setError(formatLoginError(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Enterprise RAG</CardTitle>
          <p className="text-muted-foreground">企业级知识库问答系统</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded text-sm">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="username">用户名</Label>
              <Input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="请输入用户名"
                autoComplete="username"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">密码</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="请输入密码"
                autoComplete="current-password"
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "登录中..." : "登录"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
