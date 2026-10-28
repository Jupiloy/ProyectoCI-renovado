import { apiRequest } from "./client"
import type { SessionResponse } from "./types"

export function getSession(): Promise<SessionResponse> {
  return apiRequest<SessionResponse>("/auth/session/")
}

export function login(email: string, password: string, csrfToken: string): Promise<SessionResponse> {
  return apiRequest<SessionResponse>("/auth/login/", {
    method: "POST",
    csrfToken,
    body: JSON.stringify({ email, password }),
  })
}

export function logout(csrfToken: string): Promise<{ authenticated: false }> {
  return apiRequest<{ authenticated: false }>("/auth/logout/", {
    method: "POST",
    csrfToken,
  })
}
