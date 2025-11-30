// client/src/api/sets.ts
import { api } from "./client";

export interface FetchSetsParams {
  q?: string;
  page?: number;
  perPage?: number;
}

export interface SetItem {
  id: number;
  year?: number;
  brand?: string;
  sport?: string;
  name?: string;
  set_name?: string;
  total_cards?: number;
}

export interface PaginatedSetsResponse {
  items: SetItem[];
  page: number;
  pages: number;
  total?: number;
}

// ------------------------------
// FETCH SETS
// ------------------------------
export async function fetchSets(
  { q = "", page = 1, perPage = 20 }: FetchSetsParams = {}
): Promise<PaginatedSetsResponse | SetItem[]> {
  const params = new URLSearchParams();

  if (q) params.set("q", q);
  params.set("page", String(page));
  params.set("per_page", String(perPage));

  // no trailing slash, and no .data (api.get already returns data)
  const url = `/api/sets?${params.toString()}`;
  return api.get(url);
}

// ------------------------------
// FETCH CARDS IN A SINGLE SET
// ------------------------------
export interface SetCard {
  id: number;
  sport?: string;
  year?: number;
  brand?: string;
  set_name?: string;
  card_number?: string | number;
  player_name?: string;
  team?: string | null;
  image_url?: string | null;
}

export interface PaginatedSetCardsResponse {
  items: SetCard[];
  page: number;
  pages: number;
  total?: number;
}

export async function fetchSetCards(
  setId: number,
  {
    page = 1,
    perPage = 500,
  }: {
    page?: number;
    perPage?: number;
  } = {}
): Promise<PaginatedSetCardsResponse | SetCard[]> {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("per_page", String(perPage));

  const url = `/api/sets/${setId}/cards?${params.toString()}`;
  return api.get(url);
}
