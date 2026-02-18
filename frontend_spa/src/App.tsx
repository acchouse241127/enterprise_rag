import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { isAuthenticated } from "./auth";
import Login from "./pages/Login";
import Home from "./pages/Home";
import KnowledgeBases from "./pages/KnowledgeBases";
import QA from "./pages/QA";
import Dashboard from "./pages/Dashboard";

function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!isAuthenticated()) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<RequireAuth><Home /></RequireAuth>} />
        <Route path="/knowledge-bases" element={<RequireAuth><KnowledgeBases /></RequireAuth>} />
        <Route path="/qa" element={<RequireAuth><QA /></RequireAuth>} />
        <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
