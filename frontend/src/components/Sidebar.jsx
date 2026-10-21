import React from 'react';
import { Filter, RotateCcw, Star } from 'lucide-react';

export const Sidebar = ({
  categories = [],
  selectedCategory = '',
  onSelectCategory,
  minPrice = '',
  maxPrice = '',
  onPriceChange,
  minRating = '',
  onRatingChange,
  sortBy = 'rating_desc',
  onSortChange,
  onReset,
}) => {
  return (
    <aside className="w-full lg:w-64 bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-6">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
          <Filter className="w-4 h-4 text-brand-600" />
          <span>Catalog Filters</span>
        </div>
        <button
          onClick={onReset}
          className="text-xs text-slate-400 hover:text-brand-600 flex items-center space-x-1 transition-colors"
          title="Reset All Filters"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset</span>
        </button>
      </div>

      {/* Sort order */}
      <div>
        <label className="text-xs font-semibold text-slate-700 block mb-2 uppercase tracking-wider">
          Sort By
        </label>
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value)}
          className="w-full p-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-800 outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 font-medium"
        >
          <option value="rating_desc">Highest Rated</option>
          <option value="rating_asc">Lowest Rated</option>
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
          <option value="title_asc">Title: A to Z</option>
        </select>
      </div>

      {/* Category Filter */}
      <div>
        <label className="text-xs font-semibold text-slate-700 block mb-2 uppercase tracking-wider">
          Category
        </label>
        <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
          <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer p-1 rounded hover:bg-slate-50">
            <input
              type="radio"
              name="sidebar_category"
              checked={!selectedCategory || selectedCategory === 'All'}
              onChange={() => onSelectCategory('')}
              className="text-brand-600 focus:ring-brand-500 rounded"
            />
            <span>All Categories</span>
          </label>
          {categories.map((cat) => (
            <label
              key={cat}
              className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer p-1 rounded hover:bg-slate-50"
            >
              <input
                type="radio"
                name="sidebar_category"
                checked={selectedCategory.toLowerCase() === cat.toLowerCase()}
                onChange={() => onSelectCategory(cat)}
                className="text-brand-600 focus:ring-brand-500 rounded"
              />
              <span className="truncate">{cat}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Price Range */}
      <div>
        <label className="text-xs font-semibold text-slate-700 block mb-2 uppercase tracking-wider">
          Price Range ($)
        </label>
        <div className="flex items-center space-x-2">
          <input
            type="number"
            min="0"
            placeholder="Min"
            value={minPrice}
            onChange={(e) => onPriceChange('min', e.target.value)}
            className="flex-1 min-w-0 p-2 text-xs bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-brand-500"
          />
          <span className="text-slate-400 text-xs">-</span>
          <input
            type="number"
            min="0"
            placeholder="Max"
            value={maxPrice}
            onChange={(e) => onPriceChange('max', e.target.value)}
            className="flex-1 min-w-0 p-2 text-xs bg-slate-50 border border-slate-200 rounded-lg outline-none focus:border-brand-500"
          />
        </div>
      </div>

      {/* Minimum Rating */}
      <div>
        <label className="text-xs font-semibold text-slate-700 block mb-2 uppercase tracking-wider">
          Minimum Rating
        </label>
        <div className="space-y-1">
          {[4.5, 4.0, 3.0].map((stars) => (
            <label
              key={stars}
              className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer p-1 rounded hover:bg-slate-50"
            >
              <input
                type="radio"
                name="sidebar_rating"
                checked={parseFloat(minRating) === stars}
                onChange={() => onRatingChange(stars.toString())}
                className="text-brand-600 focus:ring-brand-500 rounded"
              />
              <div className="flex items-center space-x-1 text-amber-500">
                <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                <span className="font-semibold text-slate-800">{stars}+ Stars</span>
              </div>
            </label>
          ))}
          <label className="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer p-1 rounded hover:bg-slate-50">
            <input
              type="radio"
              name="sidebar_rating"
              checked={!minRating}
              onChange={() => onRatingChange('')}
              className="text-brand-600 focus:ring-brand-500 rounded"
            />
            <span>Any Rating</span>
          </label>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
