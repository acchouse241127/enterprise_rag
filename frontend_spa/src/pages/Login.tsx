import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api";
import { setToken } from "../auth";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    try {
      const res = await login(username, password);
      const data = res as { code?: number; data?: { access_token: string }; message?: string };
      if (data.code === 0 && data.data?.access_token) {
        setToken(data.data.access_token);
        navigate("/", { replace: true });
      } else {
        setErr((data as { detail?: string }).detail || data.message || "登录失败");
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "网络错误");
    }
  }

  return (
    <div style={{ maxWidth: 360, margin: "80px auto", padding: 24, border: "1px solid #eee", borderRadius: 8 }}>
      <h1 style={{ marginTop: 0 }}>Enterprise RAG 登录</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 12 }}>
          <input
            type="text"
            placeholder="用户名"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={{ width: "100%", padding: 8 }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <input
            type="password"
            placeholder="密码"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: "100%", padding: 8 }}
          />
        </div>
        {err && <p style={{ color: "red", fontSize: 14 }}>{err}</p>}
        <button type="submit" style={{ width: "100%", padding: 10 }}>登录</button>
      </form>
    </div>
  );
}
