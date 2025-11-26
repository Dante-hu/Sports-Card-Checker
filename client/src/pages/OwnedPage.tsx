// client/src/pages/OwnedPage.tsx
import { useEffect, useState } from "react";
import {
  fetchOwned,
  deleteOwnedCard,
  type OwnedCard,
} from "../api/owned";

interface Card {
  id?: number;
  year?: number;
  brand?: string;
  set_name?: string;
  player_name?: string;
  card_number?: string | number;
  team?: string | null;
  image_url?: string | null;
}

export default function OwnedPage() {
  const [items, setItems] = useState<OwnedCard[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState<number>(1);
  const [pages, setPages] = useState<number>(1);
  const [hasNext, setHasNext] = useState<boolean>(false);
  const [hasPrev, setHasPrev] = useState<boolean>(false);

  const [toast, setToast] = useState<string | null>(null);
  const [selectedOwned, setSelectedOwned] = useState<OwnedCard | null>(null);

  // Popup for confirm remove
  const [showRemoveDialog, setShowRemoveDialog] = useState<boolean>(false);
  const [removeCount, setRemoveCount] = useState<number>(1);

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  }

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetchOwned({ page })
      .then((data: any) => {
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
        console.error("Error fetching owned:", err);
        setError(err?.message || "Failed to load owned cards");
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

  function handleOwnedClick(item: OwnedCard): void {
    setSelectedOwned(item);
    setShowRemoveDialog(false);
    setRemoveCount(1);
  }

  function closeSelected(): void {
    setSelectedOwned(null);
    setShowRemoveDialog(false);
    setRemoveCount(1);
  }

  // Clicked "Remove from Owned" in main overlay
  function handleRemoveClicked(): void {
    if (!selectedOwned) return;
    const qty = selectedOwned.quantity ?? 1;

    setRemoveCount(1);      // default
    setShowRemoveDialog(true); // always show popup now
  }

  // Actually call API and update state
  async function confirmAndRemove(count: number): Promise<void> {
    if (!selectedOwned) return;

    const currentQty = selectedOwned.quantity ?? 1;
    const safeCount = Math.min(Math.max(count, 1), currentQty);

    try {
      const res = await deleteOwnedCard(selectedOwned.id, safeCount);

      if (res && res.deleted) {
        // All copies removed -> remove from list
        setItems((prev) =>
          prev.filter((i) => i.id !== selectedOwned.id)
        );
      } else if (res && res.owned) {
        // Some remain -> update that item
        const updated = res.owned;
        setItems((prev) =>
          prev.map((i) =>
            i.id === selectedOwned.id ? { ...i, ...updated } : i
          )
        );
      } else {
        // Fallback: if API didn't send structured info
        setItems((prev) =>
          safeCount >= currentQty
            ? prev.filter((i) => i.id !== selectedOwned.id)
            : prev
        );
      }

      showToast(
        safeCount > 1
          ? `Removed ${safeCount} copies from Owned`
          : "Removed 1 copy from Owned"
      );
      closeSelected();
    } catch (err: any) {
      console.error("Failed to remove owned:", err);
      showToast(err?.message || "Failed to remove from Owned");
    }
  }

  return (
    <div className="owned-page">
      {/* toast bottom-right */}
      {toast && <div className="cards-toast">{toast}</div>}

      {/* header */}
      <div className="cards-header">
        <div>
          <h1 className="cards-title">Owned Cards</h1>
        </div>
      </div>

      {loading && <p className="cards-status">Loading owned cards…</p>}
      {!loading && error && (
        <p className="cards-status cards-status-error">Error: {error}</p>
      )}
      {!loading && !error && items.length === 0 && (
        <p className="cards-status">You don&apos;t own any cards yet.</p>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className="cards-grid">
            {items.map((owned) => {
              const card = (owned.card || {}) as Card;

              const raw = card.image_url ?? "";
              const trimmed = raw ? raw.toString().trim() : "";
              const hasImage =
                trimmed !== "" &&
                trimmed.toLowerCase() !== "null" &&
                trimmed.toLowerCase() !== "none";

              return (
                <div
                  key={owned.id}
                  className="card-tile card-tile--clickable"
                  onClick={() => handleOwnedClick(owned)}
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
                      {owned.quantity ? ` • x${owned.quantity}` : ""}
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

      {/* main overlay for card details */}
      {selectedOwned && (
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

            {(() => {
              const card = (selectedOwned.card || {}) as Card;

              const raw = card.image_url ?? "";
              const trimmed = raw ? raw.toString().trim() : "";
              const hasImage =
                trimmed !== "" &&
                trimmed.toLowerCase() !== "null" &&
                trimmed.toLowerCase() !== "none";

              const qty = selectedOwned.quantity ?? 1;

              return (
                <>
                  <h2 className="card-overlay-title">
                    {card.year} {card.brand}
                  </h2>
                  <p className="card-overlay-subtitle">
                    {card.player_name} • #{card.card_number}
                    {card.team ? ` • ${card.team}` : ""} • {card.set_name}
                    {qty ? ` • Quantity: ${qty}` : ""}
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
                </>
              );
            })()}

            <div className="card-overlay-actions">
              <button
                className="card-overlay-button"
                onClick={handleRemoveClicked}
              >
                Remove from Owned
              </button>
            </div>

            {/* SECOND POPUP: confirm (and maybe how many) */}
            {showRemoveDialog && selectedOwned && (
              <div className="card-overlay mt-4">
                <div
                  className="card-overlay-inner max-w-sm mx-auto"
                  onClick={(e) => e.stopPropagation()}
                >
                  {(() => {
                    const qty = selectedOwned.quantity ?? 1;

                    return (
                      <>
                        <h3 className="card-overlay-title text-lg mb-2">
                          {qty > 1
                            ? "How many copies do you want to remove?"
                            : "Remove this card from Owned?"}
                        </h3>
                        <p className="text-sm text-slate-200 mb-3">
                          You currently own{" "}
                          <strong>{qty}</strong> copy
                          {qty > 1 ? "ies" : ""} of this card.
                        </p>

                        {qty > 1 && (
                          <div className="flex items-center gap-2 mb-4">
                            <label className="text-sm text-slate-200">
                              Quantity to remove:
                            </label>
                            <input
                              type="number"
                              min={1}
                              max={qty}
                              value={removeCount}
                              onChange={(e) => {
                                const val = Number(e.target.value) || 1;
                                const clamped = Math.min(
                                  Math.max(val, 1),
                                  qty
                                );
                                setRemoveCount(clamped);
                              }}
                              className="w-20 rounded-md border border-slate-600 bg-slate-900 px-2 py-1 text-sm"
                            />
                          </div>
                        )}

                        <div className="flex justify-end gap-2">
                          <button
                            className="px-3 py-1.5 rounded-lg text-sm bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-medium"
                            onClick={() =>
                              confirmAndRemove(
                                selectedOwned.quantity && selectedOwned.quantity > 1
                                  ? removeCount
                                  : 1
                              )
                            }
                          >
                            Confirm
                          </button>
                          <button
                            className="px-3 py-1.5 rounded-lg text-sm border border-slate-600 bg-slate-900 hover:bg-slate-800"
                            onClick={() => {
                              setShowRemoveDialog(false);
                              setRemoveCount(1);
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      </>
                    );
                  })()}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
