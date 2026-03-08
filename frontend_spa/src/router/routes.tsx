import { lazy, Suspense } from "react";
import { Navigate } from "react-router-dom";
import { AppLayout } from "@/components/layout";
import { useAuthStore } from "@/stores/auth-store";

// 懒加载页面组件
const Login = lazy(() => import("@/pages/Login"));
const Home = lazy(() => import("@/pages/Home"));
const QA = lazy(() => import("@/pages/QA"));
const KnowledgeBases = lazy(() => import("@/pages/KnowledgeBases"));
const KnowledgeBaseDetail = lazy(() => import("@/pages/KnowledgeBaseDetail"));
const KnowledgeBaseEdit = lazy(() => import("@/pages/KnowledgeBaseEdit"));
const Conversations = lazy(() => import("@/pages/Conversations"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Tasks = lazy(() => import("@/pages/Tasks"));
const FolderSync = lazy(() => import("@/pages/FolderSync"));
const ShareView = lazy(() => import("@/pages/ShareView"));

// 加载中组件
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-[50vh]">
      <p className="text-muted-foreground">加载中...</p>
    </div>
  );
}

// 认证守卫
function RequireAuth() {
  const token = useAuthStore((s) => s.token);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <AppLayout />;
}

// 路由配置
export const routes = [
  // 公开路由
  {
    path: "/login",
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <Login />
      </Suspense>
    ),
  },
  {
    path: "/share/:shareId",
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <ShareView />
      </Suspense>
    ),
  },
  // 需要认证的路由（显式 path 确保子路由匹配后 Outlet 正确切换）
  {
    path: "/",
    element: <RequireAuth />,
    children: [
      { index: true, element: <Home /> },
      { path: "qa", element: <QA /> },
      { path: "kb", element: <KnowledgeBases /> },
      { path: "kb/:id", element: <KnowledgeBaseDetail /> },
      { path: "kb/:id/edit", element: <KnowledgeBaseEdit /> },
      { path: "conversations", element: <Conversations /> },
      { path: "conversations/:id", element: <Conversations /> },
      { path: "dashboard", element: <Dashboard /> },
      { path: "tasks", element: <Tasks /> },
      { path: "folder-sync", element: <FolderSync /> },
    ],
  },
  // 重定向旧路由
  {
    path: "knowledge-bases",
    element: <Navigate to="/kb" replace />,
  },
  {
    path: "knowledge-bases/:id",
    element: <Navigate to="/kb/:id" replace />,
  },
  // 404
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
];
