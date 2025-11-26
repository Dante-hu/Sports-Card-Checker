import React from "react";

type PaginationProps = {
  page: number;
  pages: number;
  hasPrev: boolean;
  hasNext: boolean;
  onPageChange: (newPage: number) => void;
};

export function Pagination({
  page,
  pages,
  hasPrev,
  hasNext,
  onPageChange,
}: PaginationProps) {
  if (pages <= 1) return null; // nothing to paginate

  return (
    <div className="flex items-center gap-3 mt-4 justify-center">
      <button
        onClick={() => hasPrev && onPageChange(page - 1)}
        disabled={!hasPrev}
        className="px-3 py-1 rounded border disabled:opacity-50"
      >
        ◀ Prev
      </button>

      <span className="text-sm">
        Page <span className="font-semibold">{page}</span> of{" "}
        <span className="font-semibold">{pages}</span>
      </span>

      <button
        onClick={() => hasNext && onPageChange(page + 1)}
        disabled={!hasNext}
        className="px-3 py-1 rounded border disabled:opacity-50"
      >
        Next ▶
      </button>
    </div>
  );
}
