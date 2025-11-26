// client/src/api/cards.ts
import { api } from "./client";

export interface FetchCardsParams {
  q?: string;
  page?: number;
  perPage?: number;
}

export interface Card {
  id: number;
  year: number;
  brand: string;
  set_name: string;
  player_name: string;
  card_number: string | number;
  team?: string | null;
}

export interface PaginatedCardsResponse {
  items: Card[];
  page: number;
  pages: number;
  total?: number;
}

export async function fetchCards(
  { q = "", page = 1, perPage = 20 }: FetchCardsParams = {}
): Promise<PaginatedCardsResponse | Card[]> {
  const params = new URLSearchParams();

  if (q) {
    params.set("q", q);
  }

  params.set("page", String(page));
  params.set("per_page", String(perPage));

  // trailing slash avoids redirect issues
  const url = `/api/cards/?${params.toString()}`;

  // api.get returns parsed JSON
  return api.get(url);
}
