// client/src/pages/WantlistPage.tsx
import { useEffect, useState } from "react";
import {
  fetchWanted,
  type WantedItem,
  type Card as WantedCard,
  deleteWantedItem,
} from "../api/wanted";
import EbayResults from "../components/EbayResults";
import { buildEbayQueryFromCard } from "../utils/ebay";

export default function WantlistPage() {
  const [items, setItems] = useState<WantedItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState<number>(1);
  const [pages, setPages] = useState<number>(1);
  const [hasNext, setHasNext] = useState<boolean>(false);
  const [hasPrev, setHasPrev] = useState<boolean>(false);

  const [toast, setToast] = useState<string | null>(null);
  const [selectedWanted, setSelectedWanted] =
    useState<WantedItem | null>(null);

  // confirm dialog for remove
  const [showRemoveDialog, setShowRemoveDialog] =
    useState<boolean>(false);

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  }

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetchWanted({ page })
      .then((data: any) => {
        console.log("wantlist response:", data);

        if (Array.isArray(data)) {
          setItems(data);
          setPages(1);
          setPage(1);
          setHasPrev(false);
          setHasNext(false);
          return;
        }

        const arr = Array.isArray(data.items) ? data.items : [];
        setItems(arr);

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
        console.error("Error fetching wantlist:", err);
        setError(err?.message || "Failed to load wantlist");
        setItems([]);

        setPages(1);
        setPage(1);
        setHasPrev(false);
        setHasNext(false);
      })
      .finally(() => setLoading(false));
  }, [page]);

  function goToPrev(): void {
    if (page > 1 && hasPrev) setPage((p) => p - 1);
  }

  function goToNext(): void {
    if (hasNext) setPage((p) => p + 1);
  }

  function handleWantedClick(item: WantedItem): void {
    setSelectedWanted(item);
    setShowRemoveDialog(false);
  }

  function closeSelected(): void {
    setSelectedWanted(null);
    setShowRemoveDialog(false);
  }

  // When they click "Remove from Wantlist" in the main overlay
  function handleRemoveClicked(): void {
    if (!selectedWanted) return;
    setShowRemoveDialog(true);
  }

  // Actually delete on confirm
  async function confirmRemove(): Promise<void> {
    if (!selectedWanted) return;

    try {
      await deleteWantedItem(selectedWanted.id);

      setItems((prev) => prev.filter((i) => i.id !== selectedWanted.id));
      showToast("Removed from Wantlist");
      closeSelected();
    } catch (err: any) {
      console.error("Failed to remove from wantlist:", err);
      showToast(err?.message || "Failed to remove from Wantlist");
    }
  }

  return (
    <div className="wantlist-page">
      {/* toast bottom-right (reuse same style as cards / owned) */}
      {toast && <div className="cards-toast">{toast}</div>}

      {/* simple header */}
      <div className="cards-header">
        <div>
          <h1 className="cards-title">Wantlist</h1>
        </div>
      </div>

      {loading && <p className="cards-status">Loading wantlist…</p>}
      {!loading && error && (
        <p className="cards-status cards-status-error">Error: {error}</p>
      )}
      {!loading && !error && items.length === 0 && (
        <p className="cards-status">
          Your wantlist is empty. Browse cards and add some!
        </p>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className="cards-grid">
            {items.map((item) => {
              const card = (item.card || {}) as WantedCard;

              const raw = (card.image_url as any) ?? "";
              const trimmed = raw ? raw.toString().trim() : "";
              const hasImage =
                trimmed !== "" &&
                trimmed.toLowerCase() !== "null" &&
                trimmed.toLowerCase() !== "none";

              return (
                <div
                  key={item.id}
                  className="card-tile card-tile--clickable"
                  onClick={() => handleWantedClick(item)}
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
                        alt={card.player_name || "Card"}
                        className="card-image"
                      />
                    ) : (
                      <div className="card-image-placeholder">
                        No image yet
                      </div>
                    )}
                  </div>

                  <div className="card-content">
                    <p className="card-player">
                      {card.player_name || "Unknown player"}
                    </p>
                    <p className="card-meta-line">
                      #{card.card_number}
                      {card.team ? ` • ${card.team}` : ""}
                    </p>
                    <p className="card-set">
                      {card.year} • {card.brand} • {card.set_name}
                    </p>
                    {item.notes && (
                      <p className="cards-note">Notes: {item.notes}</p>
                    )}
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

      {/* overlay for selected wantlist item + eBay on the right */}
      {selectedWanted && (
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

            {(() => {
              const card = (selectedWanted.card || {}) as WantedCard;

              const raw = (card.image_url as any) ?? "";
              const trimmed = raw ? raw.toString().trim() : "";
              const hasImage =
                trimmed !== "" &&
                trimmed.toLowerCase() !== "null" &&
                trimmed.toLowerCase() !== "none";

              const ebayQuery = buildEbayQueryFromCard(card);

              return (
                <>
                  {/* LEFT COLUMN: card details + notes + remove */}
                  <div
                    style={{
                      flex: "0 0 280px",
                      maxWidth: "100%",
                    }}
                  >
                    <h2 className="card-overlay-title">
                      {card.year} {card.brand}
                    </h2>
                    <p className="card-overlay-subtitle">
                      {card.player_name} • #{card.card_number}
                      {card.team ? ` • ${card.team}` : ""} • {card.set_name}
                    </p>

                    {hasImage ? (
                      <img
                        src={trimmed}
                        alt={card.player_name || "Card"}
                        className="card-overlay-image"
                      />
                    ) : (
                      <div className="card-overlay-image-placeholder">
                        No image available
                      </div>
                    )}

                    {selectedWanted.notes && (
                      <p className="mt-3 text-sm text-slate-200">
                        Notes: {selectedWanted.notes}
                      </p>
                    )}

                    <div className="card-overlay-actions">
                      <button
                        className="card-overlay-button"
                        onClick={handleRemoveClicked}
                      >
                        Remove from Wantlist
                      </button>
                    </div>

                    {/* Confirm remove popup */}
                    {showRemoveDialog && (
                      <div className="card-overlay mt-4">
                        <div
                          className="card-overlay-inner max-w-sm mx-auto"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <h3 className="card-overlay-title text-lg mb-2">
                            Remove from Wantlist?
                          </h3>
                          <p className="text-sm text-slate-200 mb-3">
                            This will remove this card from your wantlist.
                          </p>
                          <div className="flex justify-end gap-2">
                            <button
                              className="px-3 py-1.5 rounded-lg text-sm bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-medium"
                              onClick={confirmRemove}
                            >
                              Confirm
                            </button>
                            <button
                              className="px-3 py-1.5 rounded-lg text-sm border border-slate-600 bg-slate-900 hover:bg-slate-800"
                              onClick={() => setShowRemoveDialog(false)}
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
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
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
