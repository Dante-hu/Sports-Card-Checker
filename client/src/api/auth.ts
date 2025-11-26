// client/src/api/auth.ts
import { api } from "./client";

export interface AuthResponse {
  id: number;
  email: string;
  // add more fields if your backend returns them
}

export function signup(
  email: string,
  password: string
): Promise<AuthResponse> {
  return api.post("/api/signup", { email, password });
}

export function login(
  email: string,
  password: string
): Promise<AuthResponse> {
  return api.post("/api/login", { email, password });
}

export function logout(): Promise<null | { success?: boolean }> {
  return api.post("/api/logout");
}

export function getMe(): Promise<any> {
  // if you want, I can create a typed MeSummary interface too
  return api.get("/api/me/summary");
}
