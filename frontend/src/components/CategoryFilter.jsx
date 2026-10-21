import React from 'react';
import { Sparkles, HeartPulse, Refrigerator, Disc3 } from 'lucide-react';

const CATEGORY_ICONS = {
  'All': Sparkles,
  'All Beauty': HeartPulse,
  'Appliances': Refrigerator,
  'Digital Music': Disc3,
};

export const CategoryFilter = ({
  categories = ['All Beauty', 'Appliances', 'Digital Music'],
  selectedCategory = 'All',
  onSelectCategory,
}) => {
  const allList = ['All', ...categories.filter((c) => c !== 'All')];

  return (
    <div className="flex items-center space-x-2 overflow-x-auto py-2 no-scrollbar">
      {allList.map((cat) => {
        const isSelected = selectedCategory.toLowerCase() === cat.toLowerCase();
        const Icon = CATEGORY_ICONS[cat] || Sparkles;

        return (
          <button
            key={cat}
            onClick={() => onSelectCategory(cat === 'All' ? '' : cat)}
            className={`inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-200 ${
              isSelected
                ? 'bg-brand-600 text-white shadow-md shadow-brand-500/25 scale-105'
                : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-200/80 shadow-sm'
            }`}
          >
            <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-white' : 'text-brand-600'}`} />
            <span>{cat}</span>
          </button>
        );
      })}
    </div>
  );
};

export default CategoryFilter;
