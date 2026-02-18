import { useEffect, useState } from "react";
import { request } from "../api";

export default function Dashboard() {
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    request("/api/retrieval/dashboard")
      .then((res) => setStats((res as { data?: Record<string, unknown> }).data ?? null))
      .catch((e) => setErr(e instanceof Error ? e.message : "加载失败"));
  }, []);

  if (err) return <p style={{ color: "red" }}>{err}</p>;
  if (!stats) return <p>加载中...</p>;
  return (
    <div style={{ padding: 24 }}>
      <h1>检索质量看板</h1>
      <pre style={{ background: "#f5f5f5", padding: 16, overflow: "auto" }}>{JSON.stringify(stats, null, 2)}</pre>
    </div>
  );
}
