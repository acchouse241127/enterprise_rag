import axios from "axios";
import { useAuthStore } from "@/stores/auth-store";

const API_BASE = import.meta.env.VITE_API_BASE || "";

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// 请求拦截：注入 token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截：401 自动登出
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

// 获取原始 token（用于 SSE 等非 axios 场景）
export function getToken(): string | null {
  return useAuthStore.getState().token;
}

// 登出
export function logout(): void {
  useAuthStore.getState().logout();
}

export { API_BASE };
