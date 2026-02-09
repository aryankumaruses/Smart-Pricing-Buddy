import { FiStar, FiClock, FiExternalLink, FiTag, FiAward } from "react-icons/fi";

const PLATFORM_COLORS = {
  uber_eats: "bg-green-100 text-green-700",
  doordash: "bg-red-100 text-red-700",
  grubhub: "bg-orange-100 text-orange-700",
  postmates: "bg-purple-100 text-purple-700",
  amazon: "bg-yellow-100 text-yellow-800",
  ebay: "bg-blue-100 text-blue-700",
  walmart: "bg-blue-100 text-blue-700",
  target: "bg-red-100 text-red-700",
  bestbuy: "bg-blue-100 text-blue-800",
  uber: "bg-gray-900 text-white",
  lyft: "bg-pink-100 text-pink-700",
  taxi: "bg-yellow-100 text-yellow-800",
  booking: "bg-blue-100 text-blue-800",
  expedia: "bg-yellow-100 text-yellow-800",
  airbnb: "bg-rose-100 text-rose-700",
  hotels_com: "bg-red-100 text-red-700",
  vrbo: "bg-indigo-100 text-indigo-700",
};

const PLATFORM_NAMES = {
  uber_eats: "Uber Eats",
  doordash: "DoorDash",
  grubhub: "Grubhub",
  postmates: "Postmates",
  amazon: "Amazon",
  ebay: "eBay",
  walmart: "Walmart",
  target: "Target",
  bestbuy: "Best Buy",
  uber: "Uber",
  lyft: "Lyft",
  taxi: "Taxi",
  booking: "Booking.com",
  expedia: "Expedia",
  airbnb: "Airbnb",
  hotels_com: "Hotels.com",
  vrbo: "Vrbo",
};

export default function ResultCard({ item, index }) {
  const platformClass = PLATFORM_COLORS[item.platform] || "bg-gray-100 text-gray-700";
  const platformName = PLATFORM_NAMES[item.platform] || item.platform;
  const isTop = index === 0;

  return (
    <div
      className={`animate-fade-in bg-white rounded-2xl border p-5 flex flex-col gap-3 transition-shadow hover:shadow-lg ${
        isTop ? "border-primary-300 ring-2 ring-primary-100" : "border-gray-100"
      }`}
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* Header row */}
      <div className="flex items-start justify-between">
        <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${platformClass}`}>
          {platformName}
        </span>
        {isTop && (
          <span className="flex items-center gap-1 px-2 py-1 bg-accent-100 text-accent-600 rounded-lg text-xs font-semibold">
            <FiAward className="text-sm" /> Best Deal
          </span>
        )}
        {item.rank && !isTop && (
          <span className="text-xs text-gray-400 font-medium">#{item.rank}</span>
        )}
      </div>

      {/* Item name */}
      <h3 className="font-semibold text-gray-900 text-sm leading-snug line-clamp-2">
        {item.item_name}
      </h3>

      {/* Price */}
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-gray-900">
          ${item.total_price?.toFixed(2)}
        </span>
        {item.base_price !== item.total_price && (
          <span className="text-sm text-gray-400 line-through">
            ${item.base_price?.toFixed(2)}
          </span>
        )}
      </div>

      {/* Savings */}
      {item.savings_vs_max > 0 && (
        <p className="text-xs text-accent-600 font-medium">
          Save ${item.savings_vs_max?.toFixed(2)} vs. most expensive option
        </p>
      )}

      {/* Fees breakdown */}
      {item.fees_breakdown && (
        <div className="text-xs text-gray-500 space-y-0.5 border-t border-gray-50 pt-2">
          <div className="flex justify-between">
            <span>Base price</span>
            <span>${item.fees_breakdown.base_price?.toFixed(2)}</span>
          </div>
          {item.fees_breakdown.delivery_fee > 0 && (
            <div className="flex justify-between">
              <span>Delivery / Shipping</span>
              <span>${item.fees_breakdown.delivery_fee?.toFixed(2)}</span>
            </div>
          )}
          {item.fees_breakdown.service_fee > 0 && (
            <div className="flex justify-between">
              <span>Service fee</span>
              <span>${item.fees_breakdown.service_fee?.toFixed(2)}</span>
            </div>
          )}
          {item.fees_breakdown.tax > 0 && (
            <div className="flex justify-between">
              <span>Tax</span>
              <span>${item.fees_breakdown.tax?.toFixed(2)}</span>
            </div>
          )}
          {item.fees_breakdown.discount > 0 && (
            <div className="flex justify-between text-accent-600 font-medium">
              <span>Discount</span>
              <span>-${item.fees_breakdown.discount?.toFixed(2)}</span>
            </div>
          )}
        </div>
      )}

      {/* Meta row */}
      <div className="flex items-center gap-4 text-xs text-gray-500 mt-auto pt-2 border-t border-gray-50">
        {item.rating && (
          <span className="flex items-center gap-1">
            <FiStar className="text-yellow-500" />
            {item.rating}
            {item.rating_count && (
              <span className="text-gray-400">({item.rating_count.toLocaleString()})</span>
            )}
          </span>
        )}
        {item.delivery_time_min && (
          <span className="flex items-center gap-1">
            <FiClock />
            {item.delivery_time_min < 120
              ? `${item.delivery_time_min} min`
              : `${Math.round(item.delivery_time_min / 60)} hrs`}
          </span>
        )}
      </div>

      {/* Deals applied */}
      {item.deals_applied?.length > 0 && (
        <div className="space-y-1">
          {item.deals_applied.map((deal, i) => (
            <div
              key={i}
              className="flex items-center gap-1.5 text-xs text-primary-600 bg-primary-50 px-2 py-1 rounded-lg"
            >
              <FiTag className="shrink-0" />
              <span className="truncate">{deal}</span>
            </div>
          ))}
        </div>
      )}

      {/* Value score bar */}
      {item.value_score != null && (
        <div className="mt-1">
          <div className="flex justify-between text-[10px] text-gray-400 mb-0.5">
            <span>Value Score</span>
            <span>{(item.value_score * 100).toFixed(0)}%</span>
          </div>
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-400 to-accent-400 rounded-full transition-all"
              style={{ width: `${Math.min(item.value_score * 100, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* CTA */}
      {item.deep_link && (
        <a
          href={item.deep_link}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 flex items-center justify-center gap-2 py-2.5 bg-primary-600 text-white rounded-xl text-sm font-semibold hover:bg-primary-700 transition-colors"
        >
          View Deal <FiExternalLink />
        </a>
      )}
    </div>
  );
}
