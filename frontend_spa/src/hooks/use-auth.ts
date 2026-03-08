import { useAuthStore } from "@/stores/auth-store";

export function useAuth() {
  const { token, username, login, logout, isAuthenticated } = useAuthStore();

  return {
    token,
    username,
    login,
    logout,
    isAuthenticated: isAuthenticated(),
  };
}
