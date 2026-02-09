import { useState } from "react";
import Header from "./components/Header";
import SearchBar from "./components/SearchBar";
import CategoryTabs from "./components/CategoryTabs";
import ResultsGrid from "./components/ResultsGrid";
import DealsBar from "./components/DealsBar";
import Footer from "./components/Footer";
import { postSearch } from "./api";

const CATEGORIES = ["food", "product", "ride", "hotel"];

export default function App() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState(null);
  const [results, setResults] = useState(null);
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTime, setSearchTime] = useState(0);
  const [error, setError] = useState(null);

  const handleSearch = async (q, cat) => {
    const searchQuery = q || query;
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const payload = { query: searchQuery };
      if (cat || category) payload.category = cat || category;

      const data = await postSearch(payload);
      setResults(data.results);
      setDeals(data.deals_found || []);
      setSearchTime(data.search_time_ms);
      if (data.category) setCategory(data.category);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* Search */}
        <SearchBar
          query={query}
          setQuery={setQuery}
          onSearch={handleSearch}
          loading={loading}
        />

        {/* Category Tabs */}
        <CategoryTabs
          categories={CATEGORIES}
          active={category}
          onChange={(c) => {
            setCategory(c);
            if (query.trim()) handleSearch(query, c);
          }}
        />

        {/* Example queries */}
        {!results && !loading && (
          <div className="mt-10 text-center">
            <p className="text-gray-500 mb-4">Try one of these searches:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                "Cheapest pizza delivery within 30 minutes",
                "Best laptop deals under $800",
                "Compare Uber vs Lyft to JFK airport",
                "Hotels in Miami under $150/night",
              ].map((example) => (
                <button
                  key={example}
                  onClick={() => {
                    setQuery(example);
                    handleSearch(example);
                  }}
                  className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-primary-400 hover:text-primary-600 transition-colors shadow-sm"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Deals */}
        {deals.length > 0 && <DealsBar deals={deals} />}

        {/* Results */}
        <ResultsGrid
          results={results}
          loading={loading}
          searchTime={searchTime}
        />
      </main>

      <Footer />
    </div>
  );
}
