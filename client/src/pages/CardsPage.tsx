// client/src/pages/CardsPage.tsx
import { useEffect, useRef, useState, type FormEvent } from "react";
import { fetchCards, autoFillCardImage } from "../api/cards";
import { addOwnedCard } from "../api/owned";
import { addWantedCard } from "../api/wanted";
import { fetchSets, type SetItem } from "../api/sets";
import EbayResults from "../components/EbayResults"; // eBay component

interface Card {
  id: number;
  sport: string;
  year: number | string;
  brand: string;
  set_name: string;
  player_name: string;
  card_number: string | number;
  team?: string | null;
  image_url?: string | null;
}

interface FiltersState {
  sport: string;
  year: string;
  brand: string;
}

function buildEbayQueryFromCard(card: Card): string {
  const parts: string[] = [];

  if (card.year) parts.push(String(card.year));
  if (card.brand) parts.push(card.brand);
  if (card.set_name) parts.push(card.set_name);
  if (card.player_name) parts.push(card.player_name);
  if (card.card_number) parts.push(`#${card.card_number}`);
  if (card.team) parts.push(card.team);

  return parts.join(" ").trim();
}

export default function CardsPage() {
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [q, setQ] = useState<string>("");
  const [search, setSearch] = useState<string>("");

  const [page, setPage] = useState<number>(1);
  const [pages, setPages] = useState<number>(1);
  const [hasNext, setHasNext] = useState<boolean>(false);
  const [hasPrev, setHasPrev] = useState<boolean>(false);

  // Filters: sport / year / brand
  const [filters, setFilters] = useState<FiltersState>({
    sport: "",
    year: "",
    brand: "",
  });

  // All sets (used just to build dropdown options globally)
  const [sets, setSets] = useState<SetItem[]>([]);

  const [selectedCard, setSelectedCard] = useState<Card | null>(null);
  const ebayQuery = selectedCard ? buildEbayQueryFromCard(selectedCard) : "";

  const [toast, setToast] = useState<string | null>(null);

  const autoImageRequestedIdsRef = useRef<Set<number>>(new Set());

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  }

  // Load ALL sets once, for dropdown options
  useEffect(() => {
    fetchSets({ page: 1, perPage: 500 }).then((data: any) => {
      const arr = Array.isArray(data) ? data : data.items;
      setSets(arr || []);
    });
  }, []);

  // Load cards from backend with search + filters + pagination
  useEffect(() => {
    setLoading(true);
    setError(null);

    const params: any = { q: search, page };

    if (filters.sport.trim()) params.sport = filters.sport.trim();
    if (filters.year.trim()) params.year = filters.year.trim();
    if (filters.brand.trim()) params.brand = filters.brand.trim();

    fetchCards(params)
      .then((data: any) => {
        console.log("cards response:", data);

        if (Array.isArray(data)) {
          setCards(data);
          setPages(1);
          setPage(1);
          setHasPrev(false);
          setHasNext(false);
          return;
        }

        const items = Array.isArray(data.items) ? data.items : [];
        setCards(items);

        const currentPage =
          typeof data.page === "number" ? data.page : page;
        const totalPages =
          typeof data.pages === "number" ? data.pages : 1;

        setPage(currentPage);
        setPages(totalPages);
        setHasPrev(currentPage > 1);
        setHasNext(currentPage < totalPages);
      })
      .catch((err: any) => {
        console.error("Error fetching cards:", err);
        setError(err?.message || "Failed to load cards");
        setCards([]);
        setPages(1);
        setPage(1);
        setHasPrev(false);
        setHasNext(false);
      })
      .finally(() => setLoading(false));
  }, [search, page, filters]);

  // Auto-fill missing images in background
  useEffect(() => {
    if (!cards || cards.length === 0) return;

    for (const card of cards) {
      const raw = card.image_url ?? "";
      const trimmed = raw.toString().trim();
      const hasImage =
        trimmed !== "" &&
        trimmed.toLowerCase() !== "null" &&
        trimmed.toLowerCase() !== "none";

      if (hasImage) continue;
      if (autoImageRequestedIdsRef.current.has(card.id)) continue;
      autoImageRequestedIdsRef.current.add(card.id);

      (async () => {
        try {
          const updated = await autoFillCardImage(card.id);

          if (updated && updated.image_url) {
            setCards((prev) =>
              prev.map((c) =>
                c.id === card.id ? { ...c, image_url: updated.image_url } : c
              )
            );

            setSelectedCard((prev) =>
              prev && prev.id === card.id
                ? { ...prev, image_url: updated.image_url }
                : prev
            );
          }
        } catch (err) {
          console.error("Auto-image failed:", err);
        }
      })();
    }
  }, [cards]);

  function handleSubmit(e: FormEvent<HTMLFormElement>): void {
    e.preventDefault();
    setPage(1);
    setSearch(q.trim());
  }

  function goToPrev(): void {
    if (page > 1 && hasPrev) setPage((p) => p - 1);
  }

  function goToNext(): void {
    if (hasNext) setPage((p) => p + 1);
  }

  function handleCardClick(card: Card): void {
    setSelectedCard(card);
  }

  function closeSelected(): void {
    setSelectedCard(null);
  }

  async function handleAddOwned(): Promise<void> {
    if (!selectedCard) return;

    try {
      await addOwnedCard(selectedCard.id, 1);
      showToast("Added to Owned");
      closeSelected();
    } catch (err: any) {
      console.error("Failed to add to Owned:", err);
      showToast(err?.message || "Failed to add card to Owned");
    }
  }

  async function handleAddWanted(): Promise<void> {
    if (!selectedCard) return;

    try {
      await addWantedCard(selectedCard.id, null);
      showToast("Added to Wantlist");
      closeSelected();
    } catch (err: any) {
      console.error("Failed to add to Wantlist:", err);
      showToast(err?.message || "Failed to add card to Wantlist");
    }
  }

  function handleClearFilters(): void {
    setFilters({
      sport: "",
      year: "",
      brand: "",
    });
    setPage(1);
  }

  // Dropdown options derived from ALL sets (not just current cards page)
  const sportOptions = Array.from(
    new Set(sets.map((s) => s.sport).filter(Boolean))
  ).sort();

  const yearOptions = Array.from(
    new Set(sets.map((s) => String(s.year)).filter(Boolean))
  )
    .sort()
    .reverse();

  const brandOptions = Array.from(
    new Set(sets.map((s) => s.brand).filter(Boolean))
  ).sort();

  return (
    <div className="cards-page">
      {toast && <div className="cards-toast">{toast}</div>}

      {/* Header + search bar */}
      <div className="cards-header">
        <div>
          <h1 className="cards-title">Cards</h1>
          {search && (
            <p className="cards-subtitle">
              Showing results for{" "}
              <span className="cards-subtitle-term">“{search}”</span>
            </p>
          )}
        </div>

        <form onSubmit={handleSubmit} className="cards-search-form">
          <input
            className="cards-search-input"
            placeholder="Search player, team, etc."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button className="cards-search-button" type="submit">
            Search
          </button>
        </form>
      </div>

      {/* Filters panel directly under search */}
      <div className="mb-4 rounded-lg border border-slate-700 bg-slate-900/60 px-4 py-3">
        <div className="flex flex-wrap gap-4 items-end">
          {/* Sport dropdown */}
          <div className="flex flex-col gap-1">
            <label className="text-xs uppercase tracking-wide text-slate-300">
              Sport
            </label>
            <select
              className="cards-input rounded-md border border-slate-600 bg-slate-950 px-3 py-1.5 text-sm"
              value={filters.sport}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, sport: e.target.value }))
              }
            >
              <option value="">All sports</option>
              {sportOptions.map((sport) => (
                <option key={sport} value={sport}>
                  {sport}
                </option>
              ))}
            </select>
          </div>

          {/* Year dropdown */}
          <div className="flex flex-col gap-1">
            <label className="text-xs uppercase tracking-wide text-slate-300">
              Year
            </label>
            <select
              className="cards-input rounded-md border border-slate-600 bg-slate-950 px-3 py-1.5 text-sm"
              value={filters.year}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, year: e.target.value }))
              }
            >
              <option value="">All years</option>
              {yearOptions.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>

          {/* Brand dropdown */}
          <div className="flex flex-col gap-1">
            <label className="text-xs uppercase tracking-wide text-slate-300">
              Brand
            </label>
            <select
              className="cards-input rounded-md border border-slate-600 bg-slate-950 px-3 py-1.5 text-sm"
              value={filters.brand}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, brand: e.target.value }))
              }
            >
              <option value="">All brands</option>
              {brandOptions.map((brand) => (
                <option key={brand} value={brand}>
                  {brand}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className="ml-auto rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium hover:bg-slate-700"
            onClick={handleClearFilters}
          >
            Clear filters
          </button>
        </div>
      </div>

      {/* Status */}
      {loading && <p className="cards-status">Loading cards…</p>}
      {!loading && error && (
        <p className="cards-status cards-status-error">Error: {error}</p>
      )}
      {!loading && !error && cards.length === 0 && (
        <p className="cards-status">No cards found.</p>
      )}

      {/* Cards grid + pagination */}
      {!loading && !error && cards.length > 0 && (
        <>
          <div className="cards-grid">
            {cards.map((card) => {
              const raw = card.image_url ?? "";
              const trimmed = raw.toString().trim();
              const hasImage =
                trimmed !== "" &&
                trimmed.toLowerCase() !== "null" &&
                trimmed.toLowerCase() !== "none";

              return (
                <div
                  key={card.id}
                  className="card-tile card-tile--clickable"
                  onClick={() => handleCardClick(card)}
                >
                  <div
                    className={
                      hasImage
                        ? "card-image-wrapper"
                        : "card-image-wrapper card-image-wrapper--empty"
                    }
                  >
                    {hasImage ? (
                      <img
                        src={trimmed}
                        alt={card.player_name}
                        className="card-image"
                      />
                    ) : (
                      <div className="card-image-placeholder">
                        No image yet
                      </div>
                    )}
                  </div>

                  <div className="card-content">
                    <p className="card-player">{card.player_name}</p>

                    <p className="card-meta-line">
                      #{card.card_number}
                      {card.team ? ` • ${card.team}` : ""}
                    </p>

                    <p className="card-set">
                      {card.year} • {card.brand} • {card.set_name}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="cards-pagination">
            <button
              onClick={goToPrev}
              disabled={!hasPrev}
              className="cards-page-button"
            >
              ◀ Prev
            </button>

            <span className="cards-page-info">
              Page <strong>{page}</strong> of <strong>{pages || 1}</strong>
            </span>

            <button
              onClick={goToNext}
              disabled={!hasNext}
              className="cards-page-button"
            >
              Next ▶
            </button>
          </div>
        </>
      )}

      {/* Overlay */}
      {selectedCard && (
        <div className="card-overlay" onClick={closeSelected}>
          <div
            className="card-overlay-inner"
            onClick={(e) => e.stopPropagation()}
            style={{
              maxWidth: "1000px",
              width: "90vw",
              display: "flex",
              gap: "1.5rem",
              alignItems: "flex-start",
              flexWrap: "wrap",
            }}
          >
            <button
              className="card-overlay-close"
              onClick={closeSelected}
              aria-label="Close"
            >
              ×
            </button>

            <div
              style={{
                flex: "0 0 280px",
                maxWidth: "100%",
              }}
            >
              <h2 className="card-overlay-title">
                {selectedCard.year} {selectedCard.brand}
              </h2>
              <p className="card-overlay-subtitle">
                {selectedCard.player_name} • #{selectedCard.card_number}
                {selectedCard.team ? ` • ${selectedCard.team}` : ""} •{" "}
                {selectedCard.set_name}
              </p>

              {(() => {
                const raw = selectedCard.image_url ?? "";
                const trimmed = raw.toString().trim();
                const hasImage =
                  trimmed !== "" &&
                  trimmed.toLowerCase() !== "null" &&
                  trimmed.toLowerCase() !== "none";

                if (!hasImage) {
                  return (
                    <div className="card-overlay-image-placeholder">
                      No image available
                    </div>
                  );
                }

                return (
                  <img
                    src={trimmed}
                    alt={selectedCard.player_name}
                    className="card-overlay-image"
                  />
                );
              })()}

              <div className="card-overlay-actions">
                <button
                  className="card-overlay-button"
                  onClick={handleAddOwned}
                >
                  Add to Owned
                </button>
                <button
                  className="card-overlay-button"
                  onClick={handleAddWanted}
                >
                  Add to Wantlist
                </button>
              </div>
            </div>

            {ebayQuery && (
              <div
                className="card-overlay-ebay"
                style={{
                  flex: "1 1 0",
                  minWidth: "260px",
                }}
              >
                <EbayResults query={ebayQuery} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
