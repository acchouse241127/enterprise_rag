import { Menu, LogOut, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";
import { useAppStore } from "@/stores/app-store";

export function AppHeader() {
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);
  const { username, logout } = useAuthStore();

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-4">
      <Button variant="ghost" size="icon" onClick={toggleSidebar}>
        <Menu className="h-5 w-5" />
      </Button>

      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1 text-sm text-muted-foreground">
          <User className="h-4 w-4" />
          {username}
        </span>
        <Button variant="ghost" size="sm" onClick={logout}>
          <LogOut className="h-4 w-4 mr-1" />
          退出
        </Button>
      </div>
    </header>
  );
}
