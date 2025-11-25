// client/src/api/auth.js
import { api } from "./client";

export function signup(email, password) {
  return api.post("/api/signup", { email, password });
}

export function login(email, password) {
  return api.post("/api/login", { email, password });
}

export function logout() {
  return api.post("/api/logout");
}

export function getMe() {
  return api.get("/api/me/summary");
}
