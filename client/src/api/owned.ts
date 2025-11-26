// client/src/api/owned.ts
import { api } from "./client";

export interface FetchOwnedParams {
  page?: number;
  perPage?: number;
}

export interface OwnedCard {
  id: number;
  quantity?: number;
  card?: any; // we can replace this with a proper Card interface if you want
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

  // match Flask blueprint url_prefix
  const path = `/api/owned-cards/?${params.toString()}`;

  return api.get(path);
}
