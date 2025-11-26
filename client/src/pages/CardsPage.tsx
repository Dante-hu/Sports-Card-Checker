// client/src/pages/CardsPage.tsx
import { useEffect, useState, type FormEvent } from "react";
import { fetchCards } from "../api/cards";

interface Card {
  id: number;
  year: number;
  brand: string;
  set_name: string;
  player_name: string;
  card_number: string | number;
  team?: string | null;
}

export default function CardsPage() {
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [q, setQ] = useState<string>(""); // text in search box
  const [search, setSearch] = useState<string>(""); // actual search term used

  const [page, setPage] = useState<number>(1);
  const [pages, setPages] = useState<number>(1);
  const [hasNext, setHasNext] = useState<boolean>(false);
  const [hasPrev, setHasPrev] = useState<boolean>(false);

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetchCards({ q: search, page })
      .then((data: any) => {
        console.log("cards response:", data); // TEMP: see shape in devtools

        if (Array.isArray(data)) {
          // fallback: old behaviour (plain array, no pagination)
          setCards(data);
          setPages(1);
          setPage(1);
          setHasPrev(false);
          setHasNext(false);
          return;
        }

        const items = Array.isArray(data.items) ? data.items : [];
        setCards(items);

        // use backend values if present, else fall back
        const currentPage =
          typeof data.page === "number" ? data.page : page;
        const totalPages =
          typeof data.pages === "number" ? data.pages : 1;

        setPage(currentPage);
        setPages(totalPages);

        // 🔑 compute hasPrev/hasNext from page + pages
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
    setPage(1); // reset to first page on new search
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

  return (
    <div>
      {/* Header + search bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <h1 className="text-2xl font-semibold">Cards</h1>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            className="rounded-xl bg-slate-900 px-3 py-2 text-sm text-slate-50 outline-none focus:ring-2 focus:ring-emerald-500/70"
            placeholder="Search player, team, etc."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button className="rounded-xl bg-emerald-500 text-slate-950 px-3 py-2 text-sm font-medium">
            Search
          </button>
        </form>
      </div>

      {/* Status messages */}
      {loading && <p className="text-sm text-slate-400">Loading cards…</p>}

      {!loading && error && (
        <p className="text-sm text-red-400">Error: {error}</p>
      )}

      {!loading && !error && cards.length === 0 && (
        <p className="text-sm text-slate-400">No cards found.</p>
      )}

      {/* Actual cards grid */}
      {!loading && !error && cards.length > 0 && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {cards.map((card) => (
              <div
                key={card.id}
                className="rounded-2xl bg-slate-900 p-3 flex flex-col gap-2 border border-slate-800"
              >
                <div className="text-xs text-slate-400">
                  {card.year} • {card.brand} • {card.set_name}
                </div>
                <div className="font-semibold text-sm">
                  {card.player_name}
                </div>
                <div className="text-xs text-slate-400">
                  #{card.card_number}{" "}
                  {card.team && <>• {card.team}</>}
                </div>

                {/* later: Add to Owned / Add to Wantlist buttons */}
              </div>
            ))}
          </div>

          {/* Pagination controls */}
          <div className="flex items-center justify-center gap-4 mt-4">
            <button
              onClick={goToPrev}
              disabled={!hasPrev}
              className="px-3 py-1 rounded-xl border border-slate-700 text-sm disabled:opacity-40"
            >
              ◀ Prev
            </button>

            <span className="text-xs text-slate-400">
              Page{" "}
              <span className="font-semibold text-slate-100">
                {page}
              </span>{" "}
              of{" "}
              <span className="font-semibold text-slate-100">
                {pages || 1}
              </span>
            </span>

            <button
              onClick={goToNext}
              disabled={!hasNext}
              className="px-3 py-1 rounded-xl border border-slate-700 text-sm disabled:opacity-40"
            >
              Next ▶
            </button>
          </div>
        </>
      )}
    </div>
  );
}
