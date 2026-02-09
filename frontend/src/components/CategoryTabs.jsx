import { FiShoppingBag, FiTruck, FiMapPin, FiHome } from "react-icons/fi";

const ICONS = {
  food: FiTruck,
  product: FiShoppingBag,
  ride: FiMapPin,
  hotel: FiHome,
};

const LABELS = {
  food: "Food Delivery",
  product: "Products",
  ride: "Rides",
  hotel: "Hotels",
};

export default function CategoryTabs({ categories, active, onChange }) {
  return (
    <div className="flex justify-center gap-2 mt-6">
      {categories.map((cat) => {
        const Icon = ICONS[cat] || FiShoppingBag;
        const isActive = active === cat;
        return (
          <button
            key={cat}
            onClick={() => onChange(cat)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all ${
              isActive
                ? "bg-primary-600 text-white shadow-md shadow-primary-200"
                : "bg-white text-gray-600 border border-gray-200 hover:border-primary-300 hover:text-primary-600"
            }`}
          >
            <Icon className="text-base" />
            {LABELS[cat]}
          </button>
        );
      })}
    </div>
  );
}
