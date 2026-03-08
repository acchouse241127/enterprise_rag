import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  MessageSquare,
  Database,
  History,
  BarChart3,
  FolderSync,
  ListTodo,
} from "lucide-react";

interface AppSidebarProps {
  collapsed: boolean;
}

const NAV_ITEMS = [
  { to: "/qa", icon: MessageSquare, label: "智能问答" },
  { to: "/kb", icon: Database, label: "知识库管理" },
  { to: "/conversations", icon: History, label: "对话记录" },
  { to: "/dashboard", icon: BarChart3, label: "数据看板" },
  { to: "/folder-sync", icon: FolderSync, label: "文件夹同步" },
  { to: "/tasks", icon: ListTodo, label: "异步任务" },
];

export function AppSidebar({ collapsed }: AppSidebarProps) {
  const location = useLocation();
  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-30 flex flex-col border-r bg-card transition-all duration-200",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center justify-center border-b">
        {collapsed ? (
          <span className="text-lg font-bold text-primary">E</span>
        ) : (
          <span className="text-lg font-bold text-primary">Enterprise RAG</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 p-2">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            
            className={cn("flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors", location.pathname === item.to ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground hover:bg-accent hover:text-accent-foreground", collapsed && "justify-center px-2")}
          >
            <item.icon className="h-5 w-5 shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </Link>        ))}
      </nav>
    </aside>
  );
}
