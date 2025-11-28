// client/src/api/ebay.ts
import { api } from "./client";

export interface EbayPrice {
  value: string;
  currency: string;
  convertedFromValue?: string;
  convertedFromCurrency?: string;
}

export interface EbayImage {
  imageUrl: string;
}

export interface EbayItemSummary {
  itemId: string;
  title: string;
  itemWebUrl: string;
  price?: EbayPrice;
  image?: EbayImage;
  thumbnailImages?: EbayImage[];
}

export interface EbaySearchResponse {
  href: string;
  total: number;
  limit: number;
  offset: number;
  itemSummaries?: EbayItemSummary[];
}

export async function searchEbay(query: string): Promise<EbaySearchResponse> {
  const params = new URLSearchParams();
  params.set("q", query);

  // Calls your Flask route: /api/ebay/search
  return api.get(`/api/ebay/search?${params.toString()}`);
}
