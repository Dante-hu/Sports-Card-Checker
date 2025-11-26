// client/src/api/client.ts

// Vite will proxy /api calls, so no hardcoded backend URL.
export const API_BASE_URL = "";

export interface RequestOptions extends RequestInit {
  headers?: Record<string, string>;
}

async function request(path: string, options: RequestOptions = {}): Promise<any> {
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

  // No content
  if (res.status === 204) {
    return null;
  }

  return res.json();
}

export const api = {
  get: (path: string): Promise<any> => request(path),

  post: (path: string, body?: any): Promise<any> =>
    request(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  del: (path: string): Promise<any> =>
    request(path, { method: "DELETE" }),
};
