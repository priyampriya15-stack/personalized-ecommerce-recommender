import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import productService from '../services/productService';
import SearchBar from '../components/SearchBar';
import ProductGrid from '../components/ProductGrid';
import ErrorMessage from '../components/ErrorMessage';
import Toast from '../components/Toast';

export const SearchResults = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryParam = searchParams.get('q') || '';
  const pageParam = parseInt(searchParams.get('page') || '1', 10);

  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const showToast = (message, type = 'success') => setToast({ message, type });

  useEffect(() => {
    if (!queryParam.trim()) {
      setProducts([]);
      setTotal(0);
      return;
    }

    const performSearch = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await productService.searchProducts(queryParam, pageParam, 16);
        if (res && res.data) {
          setProducts(res.data.products || []);
          setTotal(res.data.total || 0);
          setTotalPages(res.data.total_pages || 1);
        }
      } catch (err) {
        setError(err.message || 'Search request failed.');
      } finally {
        setLoading(false);
      }
    };

    performSearch();
  }, [queryParam, pageParam]);

  const handleSearchSubmit = (newQuery) => {
    setSearchParams({ q: newQuery, page: '1' });
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setSearchParams({ q: queryParam, page: newPage.toString() });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      {/* Search Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-brand-600 mb-1">
            <Search className="w-4 h-4" />
            <span className="text-xs font-bold uppercase tracking-wider">Search Results</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900">
            {queryParam ? `Matches for "${queryParam}"` : 'Product Search'}
          </h1>
          {queryParam && (
            <p className="text-xs text-slate-500 mt-1">
              Found {total.toLocaleString()} products in catalog
            </p>
          )}
        </div>

        <div className="w-full md:w-80">
          <SearchBar initialValue={queryParam} onSearch={handleSearchSubmit} />
        </div>
      </div>

      {/* Main Content */}
      {error ? (
        <ErrorMessage
          title="Search Failed"
          message={error}
          onRetry={() => setSearchParams({ q: queryParam, page: pageParam.toString() })}
        />
      ) : (
        <>
          <ProductGrid
            products={products}
            loading={loading}
            emptyTitle={queryParam ? `No results for "${queryParam}"` : 'Enter a search term'}
            emptyMessage={
              queryParam
                ? 'Try checking for typos or searching for more general terms like "cream", "album", or "filter".'
                : 'Search through 8,300+ items across All Beauty, Appliances, and Digital Music.'
            }
            onToast={showToast}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-6 border-t border-slate-200">
              <span className="text-xs text-slate-500">
                Page {pageParam} of {totalPages}
              </span>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handlePageChange(pageParam - 1)}
                  disabled={pageParam <= 1 || loading}
                  className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Previous</span>
                </button>

                <button
                  onClick={() => handlePageChange(pageParam + 1)}
                  disabled={pageParam >= totalPages || loading}
                  className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition-colors"
                >
                  <span>Next</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default SearchResults;
