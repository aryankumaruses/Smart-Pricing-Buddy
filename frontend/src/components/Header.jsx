import { FiDollarSign } from "react-icons/fi";

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-primary-600 flex items-center justify-center">
            <FiDollarSign className="text-white text-lg" />
          </div>
          <span className="text-xl font-bold text-gray-900">
            Smart<span className="text-primary-600">Dealer</span>
          </span>
        </div>

        <nav className="hidden sm:flex items-center gap-6 text-sm text-gray-600">
          <a href="#" className="hover:text-primary-600 transition-colors">How it works</a>
          <a href="#" className="hover:text-primary-600 transition-colors">About</a>
          <button className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors">
            Sign In
          </button>
        </nav>
      </div>
    </header>
  );
}
