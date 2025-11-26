import { useEffect, useState } from "react";
import { fetchOwned } from "../api/owned";

interface Card {
  id?: number;
  year?: number;
  brand?: string;
  set_name?: string;
  player_name?: string;
  card_number?: string | number;
  team?: string | null;
}

interface OwnedItem {
  id: number;
  quantity?: number;
  card?: Card | null;
}

export default function OwnedPage() {
  const [items, setItems] = useState<OwnedItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState<number>(1);
  const [pages, setPages] = useState<number>(1);

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetchOwned({ page })
      .then((data: any) => {
        console.log("owned response:", data);

        if (Array.isArray(data)) {
          setItems(data);
          setPage(1);
          setPages(1);
          return;
        }

        const resultItems = Array.isArray(data.items) ? data.items : [];
        setItems(resultItems);

        const currentPage =
          typeof data.page === "number" ? data.page : page;
        const totalPages =
          typeof data.pages === "number" ? data.pages : 1;

        setPage(currentPage);
        setPages(totalPages);
      })
      .catch((err: any) => {
        console.error("Error fetching owned cards:", err);
        setError(err?.message || "Failed to load owned cards");
        setItems([]);
        setPage(1);
        setPages(1);
      })
      .finally(() => setLoading(false));
  }, [page]);

  function goToPrev() {
    if (page > 1) setPage((p) => p - 1);
  }

  function goToNext() {
    if (page < pages) setPage((p) => p + 1);
  }

  return (
    
    <div className="cards-page">
      {/* Header that matches CardsPage */}
      <div className="cards-header">
        <div>
          <h1 className="cards-title">My Owned Cards</h1>
        </div>
      </div>

      {/* Status messages (same style names as Cards) */}
      {loading && <p className="cards-status">Loading…</p>}

      {!loading && error && (
        <p className="cards-status cards-status-error">Error: {error}</p>
      )}

      {!loading && !error && items.length === 0 && (
        <p className="cards-status">
          You don&apos;t have any owned cards yet.
        </p>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className="cards-grid">
            {items.map((owned) => {
              const card: Card = owned.card || {};

              return (
                <div key={owned.id} className="card-tile">
                  <div className="card-content">
                    <p className="card-player">{card.player_name}</p>

                    <p className="card-meta-line">
                      #{card.card_number}
                      {card.team ? ` • ${card.team}` : ""}
                    </p>

                    <p className="card-set">
                      {card.year} • {card.brand} • {card.set_name}
                    </p>

                    {typeof owned.quantity === "number" && (
                      <p className="card-meta-line">
                        Quantity: {owned.quantity}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination, using same pattern as CardsPage */}
          <div className="cards-pagination">
            <button
              onClick={goToPrev}
              disabled={page <= 1}
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
              disabled={page >= pages}
              className="cards-page-button"
            >
              Next ▶
            </button>
          </div>
        </>
      )}
    </div>
  );
}
