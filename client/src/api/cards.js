// client/src/api/cards.js
import { api } from "./client";

export async function fetchCards(query) {
  const search = query ? `?q=${encodeURIComponent(query)}` : "";
  return api.get(`/api/cards/${search}`);
}
