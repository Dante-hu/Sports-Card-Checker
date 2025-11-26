// client/src/pages/CardsPage.tsx
import { useEffect, useState, type FormEvent } from "react";
import { fetchCards } from "../api/cards";
import { addOwnedCard } from "../api/owned";
import { addWantedCard } from "../api/wanted";

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

  // Expanded card
  const [selectedCard, setSelectedCard] = useState<Card | null>(null);

  // Notification toast
  const [toast, setToast] = useState<string | null>(null);

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  }

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetchCards({ q: search, page })
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
  }, [search, page]);

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

  // Click card
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
          <button className="cards-search-button">Search</button>
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

      {/* Enlarged card overlay */}
      {selectedCard && (
        <div className="card-overlay" onClick={closeSelected}>
          <div
            className="card-overlay-inner"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="card-overlay-close"
              onClick={closeSelected}
              aria-label="Close"
            >
              ×
            </button>

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
        </div>
      )}
    </div>
  );
}
