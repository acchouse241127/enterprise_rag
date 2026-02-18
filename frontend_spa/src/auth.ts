const TOKEN_KEY = "enterprise_rag_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
  window.location.href = "/login";
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
