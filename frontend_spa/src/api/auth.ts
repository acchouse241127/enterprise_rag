import { apiClient } from "./client";
import type { LoginResponse, MeResponse } from "./types";

export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>("/api/auth/login", {
    username,
    password,
  });
  return response.data;
}

export async function getMe(): Promise<MeResponse> {
  const response = await apiClient.get<MeResponse>("/api/auth/me");
  return response.data;
}
