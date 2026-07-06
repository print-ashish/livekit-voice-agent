const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getMe() {
  const res = await fetch(`${API}/auth/me`, { credentials: "include" });
  if (!res.ok) throw new Error("unauthorized");
  return res.json();
}

export async function logout() {
  await fetch(`${API}/auth/logout`, { method: "POST", credentials: "include" });
}

export async function getLiveKitToken() {
  const res = await fetch(`${API}/api/livekit/token`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to get LiveKit token");
  }
  return res.json();
}

export const loginUrl = `${API}/auth/google`;
