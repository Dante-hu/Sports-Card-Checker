// client/src/pages/SetsPage.tsx
import { useEffect, useState, type FormEvent } from "react";
import { fetchSets } from "../api/sets";

interface SetItem {
  id: number;
  year?: number;
  brand?: string;
  sport?: string;
  name?: string;
  set_name?: string;
  total_cards?: number;
}

export default function SetsPage() {
  const [sets, setSets] = useState<SetItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [q, setQ] = useState<string>(""); // search input
  const [search, setSearch] = useState<string>(""); // actual search term

  const [page, setPage] = useState<number>(1);
  const [pages, setPages] = useState<number>(1);

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetchSets({ q: search, page })
      .then((data: any) => {
        console.log("sets response:", data);

        if (Array.isArray(data)) {
          // fallback if backend returned plain array
          setSets(data);
          setPages(1);
          setPage(1);
          return;
        }

        const items = Array.isArray(data.items) ? data.items : [];
        setSets(items);

        const currentPage =
          typeof data.page === "number" ? data.page : page;
        const totalPages =
          typeof data.pages === "number" ? data.pages : 1;

        setPage(currentPage);
        setPages(totalPages);
      })
      .catch((err: any) => {
        console.error("Error fetching sets:", err);
        setError(err?.message || "Failed to load sets");
        setSets([]);
        setPages(1);
        setPage(1);
      })
      .finally(() => setLoading(false));
  }, [search, page]);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPage(1);
    setSearch(q.trim());
  }

  function goToPrev() {
    if (page > 1) setPage((p) => p - 1);
  }

  function goToNext() {
    if (page < pages) setPage((p) => p + 1);
  }

  return (
    <div>
      {/* Header + search bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <h1 className="text-2xl font-semibold">Sets</h1>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            className="rounded-xl bg-slate-900 px-3 py-2 text-sm text-slate-50 outline-none focus:ring-2 focus:ring-emerald-500/70"
            placeholder="Search set name, brand, year…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button className="rounded-xl bg-emerald-500 text-slate-950 px-3 py-2 text-sm font-medium">
            Search
          </button>
        </form>
      </div>

      {/* Status */}
      {loading && <p className="text-sm text-slate-400">Loading sets…</p>}
      {!loading && error && (
        <p className="text-sm text-red-400">Error: {error}</p>
      )}
      {!loading && !error && sets.length === 0 && (
        <p className="text-sm text-slate-400">No sets found.</p>
      )}

      {/* Grid */}
      {!loading && !error && sets.length > 0 && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sets.map((setItem) => (
              <div
                key={setItem.id}
                className="rounded-2xl bg-slate-900 p-3 flex flex-col gap-2 border border-slate-800"
              >
                <div className="text-xs text-slate-400">
                  {setItem.year} • {setItem.brand} • {setItem.sport}
                </div>
                <div className="font-semibold text-sm">
                  {setItem.name || setItem.set_name}
                </div>
                {typeof setItem.total_cards === "number" && (
                  <div className="text-xs text-slate-400">
                    {setItem.total_cards} cards in set
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-center gap-4 mt-4">
            <button
              onClick={goToPrev}
              disabled={page <= 1}
              className="px-3 py-1 rounded-xl border border-slate-700 text-sm disabled:opacity-40"
            >
              ◀ Prev
            </button>

            <span className="text-xs text-slate-400">
              Page{" "}
              <span className="font-semibold text-slate-100">{page}</span> of{" "}
              <span className="font-semibold text-slate-100">
                {pages || 1}
              </span>
            </span>

            <button
              onClick={goToNext}
              disabled={page >= pages}
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
