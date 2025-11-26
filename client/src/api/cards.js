// client/src/api/cards.js
import { api } from "./client";

// Supports search + pagination
export async function fetchCards({ q = "", page = 1, perPage = 20 } = {}) {
  const params = new URLSearchParams();

  if (q) {
    params.set("q", q);
  }
  params.set("page", page);
  params.set("per_page", perPage);

  // use trailing slash to avoid the redirect you saw earlier
  const url = `/api/cards/?${params.toString()}`;

  // api.get should return the parsed JSON (same as before)
  return api.get(url);
}
