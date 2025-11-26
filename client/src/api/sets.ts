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

export async function fetchSets(
  { q = "", page = 1, perPage = 20 }: FetchSetsParams = {}
): Promise<PaginatedSetsResponse | SetItem[]> {
  const params = new URLSearchParams();

  if (q) {
    params.set("q", q);
  }

  params.set("page", String(page));
  params.set("per_page", String(perPage));

  const url = `/api/sets/?${params.toString()}`;

  return api.get(url);
}
