const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "session";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function authFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    credentials: "include",
    headers: {
      ...authHeaders(),
      ...options.headers,
    },
  });
}

export async function getMe() {
  const res = await authFetch(`${API}/auth/me`);
  if (!res.ok) throw new Error("unauthorized");
  return res.json();
}

export async function logout() {
  clearToken();
  await authFetch(`${API}/auth/logout`, { method: "POST" });
}

export async function getLiveKitToken() {
  const res = await authFetch(`${API}/api/livekit/token`, { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to get LiveKit token");
  }
  return res.json();
}

export const loginUrl = `${API}/auth/google`;
