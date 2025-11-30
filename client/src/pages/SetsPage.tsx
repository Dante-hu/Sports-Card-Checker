// client/src/pages/SetsPage.tsx
import { useEffect, useState } from "react";
import { fetchOwned, deleteOwnedCard, type OwnedCard } from "../api/owned";
import {fetchSets,
  fetchSetCards,
  type SetItem,
  type SetCard,
} from "../api/sets";
import EbayResults from "../components/EbayResults";
import { buildEbayQueryFromCard } from "../utils/ebay";

export default function SetsPage() {
  const [sets, setSets] = useState<SetItem[]>([]);
  const [owned, setOwned] = useState<OwnedCard[]>([]);

  const [view, setView] = useState<"sets" | "cards">("sets");
  const [selectedSet, setSelectedSet] = useState<SetItem | null>(null);
  const [setCards, setSetCards] = useState<SetCard[]>([]);

  const [toast, setToast] = useState<string | null>(null);
  const [selectedOwned, setSelectedOwned] = useState<OwnedCard | null>(null);
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);
  const [removeCount, setRemoveCount] = useState(1);

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  }

  useEffect(() => {
    fetchSets({ page: 1, perPage: 500 }).then((data) => {
      const arr = Array.isArray(data) ? data : data.items;
      setSets(arr);
    });

    fetchOwned({ page: 1, perPage: 500 }).then((data) => {
      const arr = Array.isArray(data) ? data : data.items;
      setOwned(arr);
    });
  }, []);

  function ownedInSet(set: SetItem): OwnedCard[] {
    const setYear = set.year;
    const setBrand = set.brand;
    const setSetName = (set.set_name ?? set.name ?? "").toString().trim();

    return owned.filter((o) => {
      const c = o.card || {};
      const cardYear = c.year;
      const cardBrand = c.brand;
      const cardSetName = (c.set_name || "").toString().trim();
      return (
        cardYear === setYear &&
        cardBrand === setBrand &&
        cardSetName === setSetName
      );
    });
  }

  async function openSet(set: SetItem) {
    setSelectedSet(set);
    setView("cards");

    const data = await fetchSetCards(set.id, { page: 1, perPage: 500 });
    const arr = Array.isArray(data) ? data : data.items;
    setSetCards(arr);
  }

  function backToSets() {
    setSelectedSet(null);
    setSetCards([]);
    setView("sets");
  }

  function handleOwnedClick(item: OwnedCard) {
    setSelectedOwned(item);
    setShowRemoveDialog(false);
    setRemoveCount(1);
  }

  function closeSelected() {
    setSelectedOwned(null);
    setShowRemoveDialog(false);
    setRemoveCount(1);
  }

  async function confirmAndRemove(count: number) {
    if (!selectedOwned) return;
    const qty = selectedOwned.quantity ?? 1;
    const safe = Math.min(Math.max(count, 1), qty);

    try {
      const res = await deleteOwnedCard(selectedOwned.id, safe);

      if (res?.owned) {
        setOwned((prev) =>
          prev.map((i) =>
            i.id === selectedOwned.id ? { ...i, ...res.owned } : i
          )
        );
      } else {
        setOwned((prev) => prev.filter((i) => i.id !== selectedOwned.id));
      }

      showToast("Removed from Owned");
      closeSelected();
    } catch {
      showToast("Failed to remove");
    }
  }

  function findOwnedForCard(card: SetCard): OwnedCard | undefined {
    if (card.id != null) {
      const foundById = owned.find((o) => o.card?.id === card.id);
      if (foundById) return foundById;
    }

    return owned.find((o) => {
      const c = o.card || {};
      return (
        c.year === card.year &&
        c.brand === card.brand &&
        (c.set_name || "").toString().trim() ===
          (card.set_name || "").toString().trim() &&
        String(c.card_number) === String(card.card_number)
      );
    });
  }

  return (
    <div className="owned-page">
      {toast && <div className="cards-toast">{toast}</div>}

      {view === "sets" && (
        <>
          <h1 className="cards-title mb-4">Sets</h1>

          <div className="cards-grid">
            {sets.map((s) => {
              const ownedCards = ownedInSet(s);

              const collected = new Set(
                ownedCards.map((o) => o.card?.card_number)
              ).size;

              const setLabelParts = [
                s.year,
                s.brand,
                s.set_name ?? s.name,
                s.sport,
              ].filter(Boolean);
              const setLabel = setLabelParts.join(" ");

              const totalInSet =
                typeof s.total_cards === "number" ? s.total_cards : "?";

              return (
                <div
                  key={s.id}
                  className="card-tile card-tile--clickable"
                  onClick={() => openSet(s)}
                >
                  <div className="card-image-wrapper card-image-wrapper--empty">
                    <div className="card-image-placeholder">Set</div>
                  </div>

                  <div className="card-content">
                    <p className="card-player">{setLabel}</p>
                    <p className="card-set">
                      Collection: {collected} / {totalInSet}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {view === "cards" && selectedSet && (
        <>
          <div className="mb-4 flex items-center justify-between">
            {(() => {
              const headerParts = [
                selectedSet.year,
                selectedSet.brand,
                selectedSet.set_name ?? selectedSet.name,
                selectedSet.sport,
              ].filter(Boolean);
              const headerTitle = headerParts.join(" ");

              return <h1 className="cards-title">{headerTitle}</h1>;
            })()}

            <button
              className="px-4 py-2 rounded bg-slate-800 hover:bg-slate-700"
              onClick={backToSets}
            >
              ← Back to Sets
            </button>
          </div>

          <div className="cards-grid">
            {setCards.map((card) => {
              const ownedEntry = findOwnedForCard(card);
              const isOwned = !!ownedEntry;

              const img = card.image_url?.trim() || "";
              const hasImg =
                img && img.toLowerCase() !== "null" && img !== "none";

              const qty = ownedEntry?.quantity ?? 0;

              return (
                <div
                  key={card.id}
                  className="card-tile card-tile--clickable"
                  style={{ opacity: isOwned ? 1 : 0.35 }}
                  onClick={
                    isOwned && ownedEntry
                      ? () => handleOwnedClick(ownedEntry)
                      : undefined
                  }
                >
                  <div
                    className={
                      hasImg
                        ? "card-image-wrapper"
                        : "card-image-wrapper card-image-wrapper--empty"
                    }
                  >
                    {hasImg ? (
                      <img src={img} className="card-image" />
                    ) : (
                      <div className="card-image-placeholder">No Image</div>
                    )}
                  </div>

                  <div className="card-content">
                    <p className="card-player">{card.player_name}</p>
                    <p className="card-meta-line">
                      #{card.card_number} •{" "}
                      {isOwned ? `x${qty || 1}` : "Missing"}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {selectedOwned && (
        <div className="card-overlay" onClick={closeSelected}>
          <div
            className="card-overlay-inner"
            onClick={(e) => e.stopPropagation()}
          >
            <button className="card-overlay-close" onClick={closeSelected}>
              ×
            </button>

            {(() => {
              const c = selectedOwned.card || {};
              const img = c.image_url?.trim() || "";
              const hasImg =
                img && img.toLowerCase() !== "null" && img !== "none";

              const ebayQuery = buildEbayQueryFromCard(c);
              const qty = selectedOwned.quantity ?? 1;

              return (
                <>
                  <h2 className="card-overlay-title">
                    {c.year} {c.brand}
                  </h2>
                  <p className="card-overlay-subtitle">
                    {c.player_name} • #{c.card_number} • {c.set_name} • x{qty}
                  </p>

                  <div className="mt-4 flex flex-col gap-4 md:flex-row">
                    <div className="md:w-1/2 flex flex-col items-center">
                      {hasImg ? (
                        <img src={img} className="card-overlay-image" />
                      ) : (
                        <div className="card-overlay-image-placeholder">
                          No image
                        </div>
                      )}

                      <div className="mt-4 w-full flex flex-col items-center">
                        <button
                          className="card-overlay-button"
                          onClick={() => setShowRemoveDialog(true)}
                        >
                          Remove from Owned
                        </button>

                        {showRemoveDialog && (
                          <div className="mt-4">
                            {qty > 1 && (
                              <input
                                className="w-20 rounded border bg-slate-900 px-2 py-1"
                                type="number"
                                min={1}
                                max={qty}
                                value={removeCount}
                                onChange={(e) =>
                                  setRemoveCount(
                                    Math.max(
                                      1,
                                      Math.min(qty, Number(e.target.value))
                                    )
                                  )
                                }
                              />
                            )}

                            <div className="flex gap-2 mt-3">
                              <button
                                className="px-3 py-1.5 rounded bg-emerald-600 text-slate-950 font-semibold"
                                onClick={() => confirmAndRemove(removeCount)}
                              >
                                Confirm
                              </button>
                              <button
                                className="px-3 py-1.5 rounded bg-slate-700"
                                onClick={() => setShowRemoveDialog(false)}
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {ebayQuery && (
                      <div className="md:w-1/2">
                        <EbayResults query={ebayQuery} />
                      </div>
                    )}
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
