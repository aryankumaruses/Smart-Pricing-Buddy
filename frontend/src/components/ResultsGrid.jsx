import ResultCard from "./ResultCard";

function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-4">
      <div className="skeleton h-4 w-24" />
      <div className="skeleton h-6 w-3/4" />
      <div className="skeleton h-4 w-full" />
      <div className="skeleton h-4 w-2/3" />
      <div className="flex justify-between mt-4">
        <div className="skeleton h-8 w-20" />
        <div className="skeleton h-8 w-24" />
      </div>
    </div>
  );
}

export default function ResultsGrid({ results, loading, searchTime }) {
  if (loading) {
    return (
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (!results) return null;

  if (results.length === 0) {
    return (
      <div className="mt-12 text-center text-gray-500">
        <p className="text-lg">No results found. Try a different search.</p>
      </div>
    );
  }

  return (
    <div className="mt-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">
          {results.length} result{results.length !== 1 ? "s" : ""} found
        </p>
        {searchTime > 0 && (
          <p className="text-xs text-gray-400">
            Searched in {searchTime}ms
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {results.map((item, i) => (
          <ResultCard key={item.id || i} item={item} index={i} />
        ))}
      </div>
    </div>
  );
}
