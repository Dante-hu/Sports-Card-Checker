// client/src/api/auth.ts
import { api } from "./client";

export interface AuthResponse {
  id: number;
  email: string;
  // add more fields if your backend returns them
}

// NOTE: we added optional securityQuestion/securityAnswer,
// but old calls signup(email, password) still work.
export function signup(
  email: string,
  password: string,
  securityQuestion?: string,
  securityAnswer?: string
): Promise<AuthResponse> {
  return api.post("/api/signup", {
    email,
    password,
    security_question: securityQuestion,
    security_answer: securityAnswer,
  });
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

// -----------------------------
// NEW: set / update security question (for logged-in user)
// -----------------------------
export function setSecurityQuestion(
  question: string,
  answer: string
): Promise<void> {
  return api
    .post("/api/security-question", { question, answer })
    .then(() => {});
}

export interface ForgotPasswordResponse {
  email: string;
  security_question: string;
}

export function forgotPasswordGetQuestion(
  email: string
): Promise<ForgotPasswordResponse> {
  return api.post("/api/forgot-password", { email });
}


export function resetPasswordWithAnswer(
  email: string,
  answer: string,
  newPassword: string
): Promise<void> {
  return api
    .post("/api/reset-password", {
      email,
      answer,
      new_password: newPassword,
    })
    .then(() => {});
}
