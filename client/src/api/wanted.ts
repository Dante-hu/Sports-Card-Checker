// client/src/api/wanted.ts
import { api } from "./client";

export interface FetchWantedParams {
  page?: number;
  perPage?: number;
}

export interface Card {
  id?: number;
  year?: number;
  brand?: string;
  set_name?: string;
  player_name?: string;
  card_number?: string | number;
  team?: string | null;
  image_url?: string | null;
}

export interface WantedItem {
  id: number;
  notes?: string | null;
  card?: Card | null;
}

export interface PaginatedWantedResponse {
  items: WantedItem[];
  page: number;
  pages: number;
  total?: number;
}

export async function fetchWanted(
  { page = 1, perPage = 20 }: FetchWantedParams = {}
): Promise<PaginatedWantedResponse | WantedItem[]> {
  const params = new URLSearchParams();

  params.set("page", String(page));
  params.set("per_page", String(perPage));

  const path = `/api/wanted?${params.toString()}`;

  return api.get(path);
}

export async function addWantedCard(
  cardId: number,
  notes: string | null = null
) {
  // 🔧 removed trailing slash to match backend route "" → /api/wanted
  return api.post("/api/wanted", {
    card_id: cardId,
    notes,
  });
}

export async function deleteWantedItem(wantedId: number) {
  return api.delete(`/api/wanted/${wantedId}`);
}
