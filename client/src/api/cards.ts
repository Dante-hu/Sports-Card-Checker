// client/src/api/cards.ts
import { api } from "./client";

export interface FetchCardsParams {
  q?: string;
  page?: number;
  perPage?: number;
  sport?: string;
  year?: number;
  brand?: string;
  set?: string; // set name
}

export interface Card {
  id: number;
  year: number;
  brand: string;
  set_name: string;
  player_name: string;
  card_number: string | number;
  team?: string | null;
  image_url?: string | null;
}

export interface PaginatedCardsResponse {
  items: Card[];
  page: number;
  pages: number;
  total?: number;
}

export async function fetchCards(
  params: FetchCardsParams = {}
): Promise<PaginatedCardsResponse | Card[]> {
  const searchParams = new URLSearchParams();

  if (params.q) {
    searchParams.set("q", params.q);
  }

  if (params.page !== undefined) {
    searchParams.set("page", String(params.page));
  }

  if (params.perPage !== undefined) {
    searchParams.set("per_page", String(params.perPage));
  }

  if (params.sport) {
    searchParams.set("sport", params.sport);
  }

  if (params.year !== undefined) {
    searchParams.set("year", String(params.year));
  }

  if (params.brand) {
    searchParams.set("brand", params.brand);
  }

  if (params.set) {
    searchParams.set("set", params.set);
  }

  // no slash before "?"
  const url = `/api/cards?${searchParams.toString()}`;
  return api.get(url);
}

export async function autoFillCardImage(cardId: number) {
  return api.post(`/api/cards/${cardId}/auto-image`);
}
