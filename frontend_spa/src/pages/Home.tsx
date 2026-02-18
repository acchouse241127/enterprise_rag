import { Link } from "react-router-dom";
import { logout } from "../auth";

export default function Home() {
  return (
    <div style={{ padding: 24 }}>
      <nav style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        <Link to="/">首页</Link>
        <Link to="/knowledge-bases">知识库</Link>
        <Link to="/qa">问答</Link>
        <Link to="/dashboard">看板</Link>
        <button type="button" onClick={logout}>退出</button>
      </nav>
      <h1>Enterprise RAG</h1>
      <p>请从上方导航进入知识库、问答或看板。</p>
    </div>
  );
}
