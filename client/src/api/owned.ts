// client/src/api/owned.ts
import { api } from "./client";

export interface FetchOwnedParams {
  page?: number;
  perPage?: number;
}

export interface OwnedCard {
  id: number;
  quantity?: number;
  card?: any;
}

export interface PaginatedOwnedResponse {
  items: OwnedCard[];
  page: number;
  pages: number;
  total?: number;
}

export async function fetchOwned(
  { page = 1, perPage = 20 }: FetchOwnedParams = {}
): Promise<PaginatedOwnedResponse | OwnedCard[]> {
  const params = new URLSearchParams();

  params.set("page", String(page));
  params.set("per_page", String(perPage));

  // note: no extra slash before ?
  const path = `/api/owned-cards?${params.toString()}`;
  return api.get(path);
}

export async function addOwnedCard(cardId: number, quantity: number = 1) {
  // POST to /api/owned-cards  (no trailing slash)
  return api.post("/api/owned-cards", {
    card_id: cardId,
    quantity,
  });
}

export async function deleteOwnedCard(
  ownedId: number,
  count: number = 1
): Promise<any> {
  const params = new URLSearchParams();
  if (count > 1) {
    params.set("count", String(count));
  }

  const qs = params.toString();
  const path = qs
    ? `/api/owned-cards/${ownedId}?${qs}`
    : `/api/owned-cards/${ownedId}`;

  return api.delete(path);}
