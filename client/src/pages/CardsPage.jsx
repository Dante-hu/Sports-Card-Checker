// client/src/pages/CardsPage.jsx
import { useEffect, useState } from "react";
import { fetchCards } from "../api/cards";

export default function CardsPage() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [q, setQ] = useState("");        // text in input
  const [search, setSearch] = useState(""); // actual search term

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetchCards(search)
      .then((data) => {
        // handle both: array OR { items: [...] }
        let items = [];

        if (Array.isArray(data)) {
          items = data;
        } else if (data && Array.isArray(data.items)) {
          items = data.items;
        } else {
          console.warn("Unexpected cards response shape:", data);
        }

        setCards(items);
      })
      .catch((err) => {
        console.error("Error fetching cards:", err);
        setError(err.message || "Failed to load cards");
        setCards([]);
      })
      .finally(() => setLoading(false));
  }, [search]);

  function handleSubmit(e) {
    e.preventDefault();
    setSearch(q.trim());
  }

  return (
    <div>
      {/* header + search */}
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

      {/* content */}
      {loading && <p className="text-sm text-slate-400">Loading cards…</p>}

      {!loading && error && (
        <p className="text-sm text-red-400">Error: {error}</p>
      )}

      {!loading && !error && cards.length === 0 && (
        <p className="text-sm text-slate-400">No cards found.</p>
      )}

      {!loading && !error && cards.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((card) => (
            <div
              key={card.id}
              className="rounded-2xl bg-slate-900 p-3 flex flex-col gap-2 border border-slate-800"
            >
              <div className="text-xs text-slate-400">
                {card.year} • {card.brand} • {card.set_name}
              </div>
              <div className="font-semibold text-sm">{card.player_name}</div>
              <div className="text-xs text-slate-400">
                #{card.card_number} {card.team && <>• {card.team}</>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
