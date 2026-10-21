import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Filter } from 'lucide-react';
import productService from '../services/productService';
import Sidebar from '../components/Sidebar';
import ProductGrid from '../components/ProductGrid';
import ErrorMessage from '../components/ErrorMessage';
import Toast from '../components/Toast';

export const Products = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Query states
  const categoryParam = searchParams.get('category') || '';
  const pageParam = parseInt(searchParams.get('page') || '1', 10);
  const minPriceParam = searchParams.get('min_price') || '';
  const maxPriceParam = searchParams.get('max_price') || '';
  const minRatingParam = searchParams.get('min_rating') || '';
  const sortParam = searchParams.get('sort') || 'rating_desc';

  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success' });
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  const showToast = (message, type = 'success') => setToast({ message, type });

  // Fetch categories on mount
  useEffect(() => {
    const fetchCats = async () => {
      try {
        const res = await productService.getCategories();
        if (res && res.data) {
          setCategories(res.data.map((c) => c.name));
        }
      } catch (err) {
        console.error('Failed to load categories:', err);
      }
    };
    fetchCats();
  }, []);

  // Fetch products when query params change
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        setError(null);

        const params = {
          page: pageParam,
          limit: 16,
          sort: sortParam,
        };
        if (categoryParam) params.category = categoryParam;
        if (minPriceParam) params.min_price = parseFloat(minPriceParam);
        if (maxPriceParam) params.max_price = parseFloat(maxPriceParam);
        if (minRatingParam) params.min_rating = parseFloat(minRatingParam);

        const res = await productService.getProducts(params);
        if (res && res.data) {
          setProducts(res.data.products || []);
          setTotal(res.data.total || 0);
          setTotalPages(res.data.total_pages || 1);
        }
      } catch (err) {
        setError(err.message || 'Failed to load products from server.');
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [categoryParam, pageParam, minPriceParam, maxPriceParam, minRatingParam, sortParam]);

  // Update query params helper
  const updateParam = (key, value) => {
    const nextParams = new URLSearchParams(searchParams);
    if (value) {
      nextParams.set(key, value);
    } else {
      nextParams.delete(key);
    }
    // Reset to page 1 on filter changes
    if (key !== 'page') {
      nextParams.set('page', '1');
    }
    setSearchParams(nextParams);
  };

  const handleResetFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      updateParam('page', newPage.toString());
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      {/* Header bar */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Product Catalog
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Showing {products.length} of {total.toLocaleString()} total verified products
            {categoryParam && <span className="font-semibold text-brand-600"> in {categoryParam}</span>}
          </p>
        </div>
      </div>

      {/* Mobile / Tablet Filter Toggle Button */}
      <div className="lg:hidden w-full mb-2">
        <button
          type="button"
          onClick={() => setMobileFiltersOpen(!mobileFiltersOpen)}
          className="w-full flex items-center justify-between px-4 py-3 bg-white border border-slate-200/80 rounded-2xl text-xs font-bold text-slate-800 shadow-sm hover:bg-slate-50 transition-colors"
        >
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-brand-600" />
            <span>Filters & Sort Options</span>
            {(categoryParam || minPriceParam || maxPriceParam || minRatingParam || (sortParam && sortParam !== 'rating_desc')) && (
              <span className="w-2 h-2 rounded-full bg-brand-500" />
            )}
          </div>
          <span className="text-[11px] text-brand-600 font-semibold">
            {mobileFiltersOpen ? 'Hide Filters ▲' : 'Show Filters ▼'}
          </span>
        </button>
      </div>

      {/* Layout with Sidebar & Products Grid */}
      <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 items-start">
        {/* Filter Sidebar */}
        <div className={`${mobileFiltersOpen ? 'block' : 'hidden'} lg:block w-full lg:w-64 flex-shrink-0`}>
          <Sidebar
            categories={categories}
            selectedCategory={categoryParam}
            onSelectCategory={(cat) => updateParam('category', cat)}
            minPrice={minPriceParam}
            maxPrice={maxPriceParam}
            onPriceChange={(type, val) => updateParam(type === 'min' ? 'min_price' : 'max_price', val)}
            minRating={minRatingParam}
            onRatingChange={(rating) => updateParam('min_rating', rating)}
            sortBy={sortParam}
            onSortChange={(sort) => updateParam('sort', sort)}
            onReset={handleResetFilters}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 w-full space-y-6">
          {error ? (
            <ErrorMessage
              message={error}
              onRetry={() => updateParam('page', pageParam.toString())}
            />
          ) : (
            <>
              <ProductGrid
                products={products}
                loading={loading}
                emptyTitle="No matching products"
                emptyMessage="No catalog items matched your selected filters. Try clearing or expanding your criteria."
                onToast={showToast}
                skeletonCount={12}
              />

              {/* Pagination Controls */}
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
      </div>
    </div>
  );
};

export default Products;
