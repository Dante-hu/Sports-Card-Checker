// client/src/pages/CardsPage.tsx
import { useEffect, useRef, useState, type FormEvent } from "react";
import { fetchCards, autoFillCardImage } from "../api/cards";
import { addOwnedCard } from "../api/owned";
import { addWantedCard } from "../api/wanted";
import EbayResults from "../components/EbayResults"; // eBay component

interface Card {
  id: number;
  year: number;
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
  set_name: string;
}

function buildEbayQueryFromCard(card: Card): string {
  const parts: string[] = [];

  if (card.year) parts.push(String(card.year));
  if (card.brand) parts.push(card.brand); // e.g. "Upper Deck"
  if (card.set_name) parts.push(card.set_name); // e.g. "Series 1", "O-Pee-Chee"
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

  // Filters
  const [filters, setFilters] = useState<FiltersState>({
    sport: "",
    year: "",
    brand: "",
    set_name: "",
  });
  const [showFilters, setShowFilters] = useState<boolean>(false);

  // Expanded card
  const [selectedCard, setSelectedCard] = useState<Card | null>(null);
  // eBay query based on selected card
  const ebayQuery = selectedCard ? buildEbayQueryFromCard(selectedCard) : "";

  // Notification toast
  const [toast, setToast] = useState<string | null>(null);

  // Track which card IDs we've already tried to auto-fill this session
  const autoImageRequestedIdsRef = useRef<Set<number>>(new Set());

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  }

  // Load cards from the backend (with search + filters + pagination)
  useEffect(() => {
    setLoading(true);
    setError(null);

    const params: any = { q: search, page };

    if (filters.sport.trim()) {
      params.sport = filters.sport.trim();
    }
    if (filters.year.trim()) {
      params.year = Number(filters.year.trim());
    }
    if (filters.brand.trim()) {
      params.brand = filters.brand.trim();
    }
    if (filters.set_name.trim()) {
      // backend expects ?set=...
      params.set = filters.set_name.trim();
    }

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

  // 🔥 Auto-fill missing images in the background (no click needed)
  useEffect(() => {
    if (!cards || cards.length === 0) return;

    for (const card of cards) {
      const raw = card.image_url ?? "";
      const trimmed = raw.toString().trim();
      const hasImage =
        trimmed !== "" &&
        trimmed.toLowerCase() !== "null" &&
        trimmed.toLowerCase() !== "none";

      // Skip cards that already have an image
      if (hasImage) continue;

      // Skip if we've already tried this card ID
      if (autoImageRequestedIdsRef.current.has(card.id)) continue;
      autoImageRequestedIdsRef.current.add(card.id);

      (async () => {
        try {
          const updated = await autoFillCardImage(card.id);

          if (updated && updated.image_url) {
            // Update card in grid
            setCards((prev) =>
              prev.map((c) =>
                c.id === card.id ? { ...c, image_url: updated.image_url } : c
              )
            );

            // If this card is currently selected in the overlay, update that too
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
    if (page > 1 && hasPrev) {
      setPage((p) => p - 1);
    }
  }

  function goToNext(): void {
    if (hasNext) {
      setPage((p) => p + 1);
    }
  }

  // Click card -> open overlay
  function handleCardClick(card: Card): void {
    setSelectedCard(card);
  }

  // Close overlay
  function closeSelected(): void {
    setSelectedCard(null);
  }

  // Add to Owned
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

  // Add to Wantlist
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
      set_name: "",
    });
    setPage(1);
  }

  function handleApplyFilters(): void {
    setPage(1);
    setShowFilters(false);
  }

  return (
    <div className="cards-page">
      {/* Bottom-right toast */}
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
          {/* Filter button beside search */}
          <button
            type="button"
            className="cards-search-button cards-filter-button"
            onClick={() => setShowFilters(true)}
          >
            Filters
          </button>
        </form>
      </div>

      {/* Status messages */}
      {loading && <p className="cards-status">Loading cards…</p>}
      {!loading && error && (
        <p className="cards-status cards-status-error">Error: {error}</p>
      )}
      {!loading && !error && cards.length === 0 && (
        <p className="cards-status">No cards found.</p>
      )}

      {/* Cards grid */}
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
                  {/* IMAGE AREA */}
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

                  {/* TEXT AREA */}
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

          {/* Pagination */}
          <div className="cards-pagination">
            <button
              onClick={goToPrev}
              disabled={!hasPrev}
              className="cards-page-button"
            >
              ◀ Prev
            </button>

            <span className="cards-page-info">
              Page <strong>{page}</strong> of{" "}
              <strong>{pages || 1}</strong>
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

      {/* Filters popup (same overlay theme as card overlay) */}
      {showFilters && (
        <div
          className="card-overlay"
          onClick={() => setShowFilters(false)}
        >
          <div
            className="card-overlay-inner"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: "420px" }}
          >
            <button
              className="card-overlay-close"
              onClick={() => setShowFilters(false)}
              aria-label="Close filters"
            >
              ×
            </button>

            <h2 className="cards-title" style={{ marginBottom: "0.75rem" }}>
              Filters
            </h2>

            <div className="cards-filters-group" style={{ marginBottom: "0.75rem" }}>
              <label
                className="cards-subtitle"
                style={{ display: "block", marginBottom: "0.25rem" }}
              >
                Sport
              </label>
              <input
                className="cards-search-input"
                placeholder="e.g. Hockey"
                value={filters.sport}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, sport: e.target.value }))
                }
              />
            </div>

            <div className="cards-filters-group" style={{ marginBottom: "0.75rem" }}>
              <label
                className="cards-subtitle"
                style={{ display: "block", marginBottom: "0.25rem" }}
              >
                Year
              </label>
              <input
                className="cards-search-input"
                placeholder="e.g. 2022"
                value={filters.year}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, year: e.target.value }))
                }
              />
            </div>

            <div className="cards-filters-group" style={{ marginBottom: "0.75rem" }}>
              <label
                className="cards-subtitle"
                style={{ display: "block", marginBottom: "0.25rem" }}
              >
                Brand
              </label>
              <input
                className="cards-search-input"
                placeholder="e.g. Upper Deck"
                value={filters.brand}
                onChange={(e) =>
                  setFilters((prev) => ({ ...prev, brand: e.target.value }))
                }
              />
            </div>

            <div className="cards-filters-group" style={{ marginBottom: "0.75rem" }}>
              <label
                className="cards-subtitle"
                style={{ display: "block", marginBottom: "0.25rem" }}
              >
                Set name
              </label>
              <input
                className="cards-search-input"
                placeholder="e.g. Series 1"
                value={filters.set_name}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    set_name: e.target.value,
                  }))
                }
              />
            </div>

            <div
              className="cards-pagination"
              style={{
                marginTop: "1rem",
                justifyContent: "flex-end",
                gap: "0.5rem",
              }}
            >
              <button
                type="button"
                className="cards-page-button"
                onClick={handleClearFilters}
              >
                Clear
              </button>
              <button
                type="button"
                className="cards-page-button"
                onClick={handleApplyFilters}
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Enlarged card overlay */}
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

            {/* LEFT COLUMN: title + card + buttons */}
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

            {/* RIGHT COLUMN: eBay listings */}
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
