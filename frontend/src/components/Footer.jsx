export default function Footer() {
  return (
    <footer className="mt-12 border-t border-gray-100 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 text-sm text-gray-500">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Smart Dealer</h4>
            <p>
              Compare prices across food delivery, e-commerce, ride-sharing, and
              hotel platforms — all in one place.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Categories</h4>
            <ul className="space-y-1">
              <li>Food Delivery</li>
              <li>Products & Electronics</li>
              <li>Ride Sharing</li>
              <li>Hotels & Accommodation</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Transparency</h4>
            <p>
              All prices include fees and taxes.  We do not accept paid
              placements. Prices are timestamped and may change.
            </p>
          </div>
        </div>
        <div className="mt-8 pt-4 border-t border-gray-100 text-center text-xs text-gray-400">
          © 2026 Smart Dealer. Prices shown are estimates unless noted.
        </div>
      </div>
    </footer>
  );
}
