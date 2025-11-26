// client/src/pages/OwnedPage.jsx
import { useEffect, useState } from "react";
import { fetchOwned } from "../api/owned";

export default function OwnedPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetchOwned({ page })
      .then((data) => {
        console.log("owned response:", data);

        if (Array.isArray(data)) {
          // fallback if backend returned a simple array
          setItems(data);
          setPage(1);
          setPages(1);
          return;
        }

        const resultItems = Array.isArray(data.items) ? data.items : [];
        setItems(resultItems);

        const currentPage = typeof data.page === "number" ? data.page : page;
        const totalPages = typeof data.pages === "number" ? data.pages : 1;

        setPage(currentPage);
        setPages(totalPages);
      })
      .catch((err) => {
        console.error("Error fetching owned cards:", err);
        setError(err.message || "Failed to load owned cards");
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
    <div>
      <h1 className="text-2xl font-semibold mb-4">My Owned Cards</h1>

      {loading && <p className="text-sm text-slate-400">Loading…</p>}

      {!loading && error && (
        <p className="text-sm text-red-400">Error: {error}</p>
      )}

      {!loading && !error && items.length === 0 && (
        <p className="text-sm text-slate-400">
          You don&apos;t have any owned cards yet.
        </p>
      )}

      {!loading && !error && items.length > 0 && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((owned) => {
              const card = owned.card || {};
              return (
                <div
                  key={owned.id}
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

                  {typeof owned.quantity === "number" && (
                    <div className="text-xs text-emerald-400">
                      Quantity: {owned.quantity}
                    </div>
                  )}

                  {/* later: remove / adjust quantity buttons here */}
                </div>
              );
            })}
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
