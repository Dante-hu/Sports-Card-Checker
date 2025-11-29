// client/src/api/client.ts
export const API_BASE_URL = "http://localhost:5000";


type RequestOptions = RequestInit & {
  // body will always be JSON string if present
  body?: string;
};

async function request(path: string, options: RequestOptions = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  // --- ERROR PATH: read body ONCE as text ---
  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    const bodyText = await res.text(); // single read

    if (bodyText) {
      try {
        const data = JSON.parse(bodyText);
        if (data && (data.error || data.message)) {
          message = data.error || data.message;
        } else {
          message = bodyText;
        }
      } catch {
        message = bodyText;
      }
    }

    throw new Error(message);
  }

  // --- SUCCESS PATH ---
  if (res.status === 204) {
    return null;
  }

  const text = await res.text(); // single read
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export const api = {
  get: (path: string) => request(path),
  post: (path: string, body?: unknown) =>
    request(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
  put: (path: string, body?: unknown) =>
    request(path, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: (path: string) =>
    request(path, {
      method: "DELETE",
    }),
};
