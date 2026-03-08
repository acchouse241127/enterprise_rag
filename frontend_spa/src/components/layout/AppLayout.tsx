import { Suspense } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { AppHeader } from "./AppHeader";
import { AppSidebar } from "./AppSidebar";
import { useAppStore } from "@/stores/app-store";
import { cn } from "@/lib/utils";

export function AppLayout() {
  const sidebarCollapsed = useAppStore((s) => s.sidebarCollapsed);
  const location = useLocation();

  return (
    <div className="flex h-screen bg-background text-foreground">
      <AppSidebar collapsed={sidebarCollapsed} />
      <div
        className={cn(
          "flex flex-1 flex-col transition-all duration-200",
          sidebarCollapsed ? "ml-16" : "ml-60"
        )}
      >
        <AppHeader />
        <main className="flex-1 overflow-auto p-6">
          <Suspense fallback={<div className="flex items-center justify-center p-8 text-muted-foreground">加载中...</div>}>
            <Outlet key={location.pathname} />
          </Suspense>
        </main>
      </div>
    </div>
  );
}
