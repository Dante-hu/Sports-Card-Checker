// client/src/api/client.js

// We now let Vite proxy /api calls to the backend,
// so we don't hardcode http://127.0.0.1:5000 here.
export const API_BASE_URL = "";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.error) {
        message = data.error;
      }
    } catch {
      const text = await res.text();
      if (text) message = text;
    }
    throw new Error(message);
  }

  if (res.status === 204) {
    return null;
  }

  return res.json();
}

export const api = {
  get: (path) => request(path),
  post: (path, body) =>
    request(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
  del: (path) => request(path, { method: "DELETE" }),
};
