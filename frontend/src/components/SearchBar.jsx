import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X } from 'lucide-react';

export const SearchBar = ({ initialValue = '', onSearch, placeholder = 'Search 8,300+ products (e.g. lotion, guitar, blender)...' }) => {
  const [query, setQuery] = useState(initialValue);
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;

    if (onSearch) {
      onSearch(trimmed);
    } else {
      navigate(`/search?q=${encodeURIComponent(trimmed)}`);
    }
  };

  const handleClear = () => {
    setQuery('');
    if (onSearch) onSearch('');
  };

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-2xl">
      <div className="relative flex items-center">
        <Search className="absolute left-4 w-4 h-4 text-slate-400 pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="w-full pl-10 sm:pl-11 pr-20 sm:pr-24 py-2 sm:py-2.5 bg-slate-100 hover:bg-slate-50 focus:bg-white text-slate-900 placeholder:text-slate-400 rounded-xl border border-transparent focus:border-brand-500 focus:ring-4 focus:ring-brand-500/10 text-xs sm:text-sm transition-all duration-200 outline-none"
        />
        {query && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-14 sm:right-16 p-1 text-slate-400 hover:text-slate-600 rounded-md"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
        <button
          type="submit"
          className="absolute right-1.5 px-2.5 sm:px-3.5 py-1 sm:py-1.5 bg-brand-600 hover:bg-brand-700 active:scale-95 text-white rounded-lg text-xs font-semibold shadow-sm transition-all"
        >
          Search
        </button>
      </div>
    </form>
  );
};

export default SearchBar;
