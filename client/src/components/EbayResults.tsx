import { useEffect, useState } from "react";
import { searchEbay, EbayItemSummary } from "../api/ebay";

interface EbayResultsProps {
  query: string;
}

export default function EbayResults({ query }: EbayResultsProps) {
  const [items, setItems] = useState<EbayItemSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!query.trim()) {
      setItems([]);
      return;
    }

    setLoading(true);
    setError(null);

    searchEbay(query)
      .then((data) => {
        setItems(data.itemSummaries ?? []);
      })
      .catch((err: any) => {
        setError(err.message || "Failed to load eBay results");
      })
      .finally(() => setLoading(false));
  }, [query]);

  if (!query.trim()) return null;

  return (
    <div className="mt-4 border rounded-lg p-3 bg-slate-900/40">
      <h2 className="font-semibold text-lg mb-2">
        eBay listings for: <span className="text-indigo-300">{query}</span>
      </h2>

      {loading && <p>Loading eBay listings…</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <p className="text-sm text-slate-300">No listings found.</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-2">
        {items.map((item) => {
          const thumb =
            item.image?.imageUrl || item.thumbnailImages?.[0]?.imageUrl;

          return (
            <a
              key={item.itemId}
              href={item.itemWebUrl}
              target="_blank"
              rel="noreferrer"
              className="flex gap-3 border border-slate-700 rounded-md p-2 hover:border-indigo-400 hover:bg-slate-800/60 transition"
            >
              {thumb && (
                <img
                  src={thumb}
                  alt={item.title}
                  className="w-16 h-16 object-cover rounded"
                />
              )}
              <div className="flex-1">
                <div className="text-sm font-medium line-clamp-2">
                  {item.title}
                </div>
                {item.price && (
                  <div className="text-sm mt-1">
                    {item.price.value} {item.price.currency}
                  </div>
                )}
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
