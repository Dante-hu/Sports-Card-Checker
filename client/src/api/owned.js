// client/src/api/owned.js
import { api } from "./client";

export async function fetchOwned({ page = 1, perPage = 20 } = {}) {
  const params = new URLSearchParams();
  params.set("page", page);
  params.set("per_page", perPage);

  // 👇 match the Flask blueprint url_prefix
  const path = `/api/owned-cards/?${params.toString()}`;

  return api.get(path);
}
