// client/src/api/wanted.js
import { api } from "./client";

export async function fetchWanted({ page = 1, perPage = 20 } = {}) {
  const params = new URLSearchParams();
  params.set("page", page);
  params.set("per_page", perPage);

  const path = `/api/wanted/?${params.toString()}`;
  return api.get(path);
}
