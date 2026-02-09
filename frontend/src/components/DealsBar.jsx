import { FiTag, FiChevronRight } from "react-icons/fi";

export default function DealsBar({ deals }) {
  if (!deals || deals.length === 0) return null;

  return (
    <div className="mt-6 p-4 bg-gradient-to-r from-primary-50 to-accent-50 border border-primary-100 rounded-2xl">
      <div className="flex items-center gap-2 mb-3">
        <FiTag className="text-primary-600" />
        <h3 className="text-sm font-semibold text-primary-700">
          Active Deals & Promotions
        </h3>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {deals.map((deal, i) => (
          <div
            key={deal.id || i}
            className="shrink-0 bg-white px-4 py-3 rounded-xl border border-primary-100 max-w-xs shadow-sm"
          >
            <p className="text-sm font-medium text-gray-900">{deal.description}</p>
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              {deal.code && (
                <span className="px-2 py-0.5 bg-primary-100 text-primary-700 rounded font-mono font-semibold">
                  {deal.code}
                </span>
              )}
              {deal.discount_percent && (
                <span className="text-accent-600 font-semibold">{deal.discount_percent}% off</span>
              )}
              {deal.discount_amount && (
                <span className="text-accent-600 font-semibold">${deal.discount_amount} off</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
