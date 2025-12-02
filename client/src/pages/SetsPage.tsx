// client/src/pages/SetsPage.tsx
import { useEffect, useState } from "react";
import {
  fetchOwned,
  deleteOwnedCard,
  addOwnedCard,
  type OwnedCard,
} from "../api/owned";
import {
  fetchSets,
  fetchSetCards,
  type SetItem,
  type SetCard,
} from "../api/sets";
import { addWantedCard } from "../api/wanted";
import EbayResults from "../components/EbayResults";
import { buildEbayQueryFromCard } from "../utils/ebay";

export default function SetsPage() {
  const [sets, setSets] = useState<SetItem[]>([]);
  const [owned, setOwned] = useState<OwnedCard[]>([]);

  const [view, setView] = useState<"sets" | "cards">("sets");
  const [selectedSet, setSelectedSet] = useState<SetItem | null>(null);
  const [setCards, setSetCards] = useState<SetCard[]>([]);

  const [toast, setToast] = useState<string | null>(null);
  const [selectedCard, setSelectedCard] = useState<SetCard | null>(null);
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);
  const [removeCount, setRemoveCount] = useState(1);

  // Filters for the Sets list
  const [sportFilter, setSportFilter] = useState<string>("");
  const [yearFilter, setYearFilter] = useState<string>("");

  // NEW: search within cards of a single set
  const [cardSearch, setCardSearch] = useState<string>("");

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  }

  useEffect(() => {
    // Load sets once; backend now returns all sets (no pagination).
    fetchSets({ page: 1, perPage: 500 }).then((data) => {
      const arr = Array.isArray(data) ? data : data.items;
      setSets(arr);
    });

    // Load owned cards for progress and overlays.
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
    setCardSearch(""); // reset search when opening a new set

    // Backend now returns ALL cards for the set in one shot.
    const data = await fetchSetCards(set.id, { page: 1, perPage: 9999 });
    const arr = Array.isArray(data) ? data : data.items;
    setSetCards(arr);
  }

  function backToSets() {
    setSelectedSet(null);
    setSetCards([]);
    setView("sets");
    setCardSearch("");
  }

  function closeSelected() {
    setSelectedCard(null);
    setShowRemoveDialog(false);
    setRemoveCount(1);
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

  function handleCardClick(card: SetCard) {
    setSelectedCard(card);
    setShowRemoveDialog(false);
    setRemoveCount(1);
  }

  async function confirmAndRemove(count: number) {
    if (!selectedCard) return;
    const ownedEntry = findOwnedForCard(selectedCard);
    if (!ownedEntry) return;

    const qty = ownedEntry.quantity ?? 1;
    const safe = Math.min(Math.max(count, 1), qty);

    try {
      const res = await deleteOwnedCard(ownedEntry.id, safe);

      if (res?.owned) {
        setOwned((prev) =>
          prev.map((i) =>
            i.id === ownedEntry.id ? { ...i, ...res.owned } : i
          )
        );
      } else {
        setOwned((prev) => prev.filter((i) => i.id !== ownedEntry.id));
      }

      showToast("Removed from Owned");
      closeSelected();
    } catch {
      showToast("Failed to remove");
    }
  }

  // ---------- SET LIST FILTERING ----------
  const uniqueSports = Array.from(new Set(sets.map((s) => s.sport))).sort();
  const uniqueYears = Array.from(
    new Set(sets.map((s) => String(s.year)))
  )
    .sort()
    .reverse();

  const filteredSets = sets.filter((s) => {
    const matchesSport = sportFilter ? s.sport === sportFilter : true;
    const matchesYear = yearFilter ? String(s.year) === yearFilter : true;
    return matchesSport && matchesYear;
  });

  // ---------- CARD SEARCH (inside a set) ----------
  const visibleCards = setCards.filter((card) => {
    if (!cardSearch.trim()) return true;
    const q = cardSearch.toLowerCase();

    const name = (card.player_name || "").toLowerCase();
    const team = (card.team || "").toLowerCase();
    const number = String(card.card_number || "").toLowerCase();

    return (
      name.includes(q) ||
      team.includes(q) ||
      number.includes(q)
    );
  });

  return (
    <div className="owned-page">
      {toast && <div className="cards-toast">{toast}</div>}

      {/* SET LIST VIEW */}
      {view === "sets" && (
        <>
          <h1 className="cards-title mb-4">Sets</h1>

          {/* Filters styled similarly to the rest of the cards UI */}
          <div className="mb-4 rounded-lg border border-slate-700 bg-slate-900/60 px-4 py-3">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="flex flex-col gap-1">
                <label className="text-xs uppercase tracking-wide text-slate-300">
                  Sport
                </label>
                <select
                  className="cards-input rounded-md border border-slate-600 bg-slate-950 px-3 py-1.5 text-sm"
                  value={sportFilter}
                  onChange={(e) => setSportFilter(e.target.value)}
                >
                  <option value="">All sports</option>
                  {uniqueSports.map((sport) => (
                    <option key={sport} value={sport}>
                      {sport}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs uppercase tracking-wide text-slate-300">
                  Year
                </label>
                <select
                  className="cards-input rounded-md border border-slate-600 bg-slate-950 px-3 py-1.5 text-sm"
                  value={yearFilter}
                  onChange={(e) => setYearFilter(e.target.value)}
                >
                  <option value="">All years</option>
                  {uniqueYears.map((year) => (
                    <option key={year} value={year}>
                      {year}
                    </option>
                  ))}
                </select>
              </div>

              <button
                className="ml-auto rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm font-medium hover:bg-slate-700"
                type="button"
                onClick={() => {
                  setSportFilter("");
                  setYearFilter("");
                }}
              >
                Clear filters
              </button>
            </div>
          </div>

          <div className="cards-grid">
            {filteredSets.map((s) => {
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

      {/* CARDS IN A SINGLE SET */}
      {view === "cards" && selectedSet && (
        <>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
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

            <div className="flex items-center gap-3">
              {/* NEW: search bar for cards in this set */}
              <input
                type="text"
                placeholder="Search cards (name, team, #)..."
                className="cards-input rounded-md border border-slate-600 bg-slate-950 px-3 py-1.5 text-sm"
                value={cardSearch}
                onChange={(e) => setCardSearch(e.target.value)}
              />

              <button
                className="rounded-md border border-slate-600 bg-slate-800 px-4 py-2 text-sm font-medium hover:bg-slate-700"
                onClick={backToSets}
              >
                ← Back to Sets
              </button>
            </div>
          </div>

          <div className="cards-grid">
            {visibleCards.map((card) => {
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
                  onClick={() => handleCardClick(card)}
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

      {/* CARD OVERLAY (OWNED OR MISSING) */}
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

            {(() => {
              const c = selectedCard;
              const ownedEntry = findOwnedForCard(c);
              const qty = ownedEntry?.quantity ?? 0;

              const img = c.image_url?.trim() || "";
              const hasImg =
                img && img.toLowerCase() !== "null" && img !== "none";

              const ebayQuery = buildEbayQueryFromCard(c as any);

              return (
                <>
                  {/* LEFT COLUMN */}
                  <div
                    style={{
                      flex: "0 0 280px",
                      maxWidth: "100%",
                    }}
                  >
                    <h2 className="card-overlay-title">
                      {c.year} {c.brand}
                    </h2>
                    <p className="card-overlay-subtitle">
                      {c.player_name} • #{c.card_number} • {c.set_name} •{" "}
                      {ownedEntry ? `x${qty}` : "Missing from your collection"}
                    </p>

                    {hasImg ? (
                      <img src={img} className="card-overlay-image" />
                    ) : (
                      <div className="card-overlay-image-placeholder">
                        No image
                      </div>
                    )}

                    {/* ACTIONS: add / wantlist / remove */}
                    <div className="mt-4 flex flex-col gap-2">
                      {/* Add to Owned */}
                      <button
                        className="card-overlay-button"
                        onClick={async () => {
                          if (!c.id) return;
                          try {
                            await addOwnedCard(c.id);

                            // Refresh owned so quantities + opacity update
                            const data = await fetchOwned({
                              page: 1,
                              perPage: 500,
                            });
                            const arr = Array.isArray(data)
                              ? data
                              : data.items;
                            setOwned(arr);

                            showToast("Added to Owned");
                          } catch {
                            showToast("Failed to add to Owned");
                          }
                        }}
                      >
                        Add to Owned
                      </button>

                      {/* Add to Wantlist */}
                      <button
                        className="card-overlay-button"
                        onClick={async () => {
                          if (!c.id) return;
                          try {
                            await addWantedCard(c.id);
                            showToast("Added to Wantlist");
                          } catch {
                            showToast("Failed to add to Wantlist");
                          }
                        }}
                      >
                        Add to Wantlist
                      </button>

                      {/* Remove from Owned (styled to match overlay) */}
                      {ownedEntry && (
                        <div className="mt-2 rounded-md border border-slate-700 bg-slate-900/70 px-3 py-2">
                          <p className="mb-2 text-xs text-slate-300">
                            You currently own <strong>x{qty}</strong> of this
                            card.
                          </p>

                          {qty > 1 && (
                            <div className="mb-2 flex items-center gap-2">
                              <span className="text-xs text-slate-300">
                                Remove:
                              </span>
                              <input
                                className="w-20 rounded-md border border-slate-600 bg-slate-950 px-2 py-1 text-sm"
                                type="number"
                                min={1}
                                max={qty}
                                value={removeCount}
                                onChange={(e) =>
                                  setRemoveCount(
                                    Math.max(
                                      1,
                                      Math.min(
                                        qty,
                                        Number(e.target.value) || 1
                                      )
                                    )
                                  )
                                }
                              />
                              <span className="text-xs text-slate-400">
                                (max {qty})
                              </span>
                            </div>
                          )}

                          <div className="flex gap-2">
                            <button
                              className="card-overlay-button"
                              onClick={() =>
                                confirmAndRemove(removeCount)
                              }
                            >
                              Confirm remove
                            </button>
                            <button
                              className="card-overlay-button"
                              onClick={() => {
                                setShowRemoveDialog(false);
                                setRemoveCount(1);
                              }}
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}
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
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
