// client/src/api/sets.js
import { api } from "./client";

export async function fetchSets({ q = "", page = 1, perPage = 20 } = {}) {
  const params = new URLSearchParams();

  if (q) {
    params.set("q", q);
  }
  params.set("page", page);
  params.set("per_page", perPage);

  const url = `/api/sets/?${params.toString()}`;
  return api.get(url); // same pattern as cards
}
