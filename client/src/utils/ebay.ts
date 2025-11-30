// client/src/utils/ebay.ts

// Minimal shape we need to build an eBay search string
export interface EbayCardLike {
  year?: number;
  brand?: string;
  set_name?: string;
  player_name?: string;
  card_number?: string | number;
  team?: string | null;
}


export function buildEbayQueryFromCard(
  card: EbayCardLike | null | undefined
): string {
  if (!card) return "";

  const parts: string[] = [];

  if (card.year) parts.push(String(card.year));
  if (card.brand) parts.push(card.brand);
  if (card.set_name) parts.push(card.set_name);
  if (card.player_name) parts.push(card.player_name);
  if (card.card_number !== undefined && card.card_number !== null) {
    parts.push(`#${card.card_number}`);
  }
  if (card.team) parts.push(card.team);

  return parts.join(" ").trim();
}
