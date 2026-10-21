import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { History as HistoryIcon, Eye, Heart, Star, ShoppingBag, CheckCircle, Clock } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import interactionService from '../services/interactionService';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import Toast from '../components/Toast';

export const History = () => {
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [typeFilter, setTypeFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const showToast = (message, type = 'success') => setToast({ message, type });

  const fetchHistory = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      setError(null);
      const res = await interactionService.getUserHistory(user.id, typeFilter || null, 50);
      if (res && res.data) {
        setHistory(res.data);
      }
    } catch (err) {
      setError(err.message || 'Failed to load interaction history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [user?.id, typeFilter]);

  const typeConfig = {
    view: { label: 'Viewed', icon: Eye, bg: 'bg-sky-50 text-sky-700 border-sky-200' },
    like: { label: 'Liked', icon: Heart, bg: 'bg-rose-50 text-rose-700 border-rose-200' },
    rating: { label: 'Rated', icon: Star, bg: 'bg-amber-50 text-amber-700 border-amber-200' },
    cart: { label: 'Added to Cart', icon: ShoppingBag, bg: 'bg-teal-50 text-teal-700 border-teal-200' },
    purchase: { label: 'Purchased', icon: CheckCircle, bg: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  };

  const filterTabs = ['', 'view', 'like', 'rating', 'cart', 'purchase'];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      <div className="pb-4 border-b border-slate-200">
        <div className="flex items-center space-x-2 text-brand-600 mb-1">
          <HistoryIcon className="w-5 h-5" />
          <span className="text-xs font-bold uppercase tracking-wider">Audit Log & Timeline</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Interaction History
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Every browsing, rating, and purchase event recorded in the database feeds your personalized model
        </p>
      </div>

      {/* Type Filter Pills */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-2 no-scrollbar">
        {filterTabs.map((t) => (
          <button
            key={t || 'all'}
            onClick={() => setTypeFilter(t)}
            className={`px-4 py-2 rounded-xl text-xs font-bold capitalize transition-all whitespace-nowrap ${
              typeFilter === t
                ? 'bg-brand-600 text-white shadow-md shadow-brand-500/25'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {t ? t : 'All Interactions'}
          </button>
        ))}
      </div>

      {/* Main List */}
      {error ? (
        <ErrorMessage message={error} onRetry={fetchHistory} />
      ) : loading ? (
        <div className="space-y-3 animate-pulse">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-16 bg-slate-100 rounded-2xl w-full" />
          ))}
        </div>
      ) : history.length === 0 ? (
        <EmptyState
          icon={HistoryIcon}
          title="No interactions recorded"
          description="Browse the catalog and view, rate, or like products to build your history timeline."
          actionText="Explore Products"
          actionLink="/products"
        />
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm divide-y divide-slate-100">
          {history.map((item) => {
            const config = typeConfig[item.interaction_type] || {
              label: item.interaction_type,
              icon: Clock,
              bg: 'bg-slate-100 text-slate-700 border-slate-200',
            };
            const Icon = config.icon;

            return (
              <div
                key={item.id}
                className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/70 transition-colors"
              >
                <div className="flex items-center space-x-4 min-w-0">
                  {item.image_url ? (
                    <img
                      src={item.image_url}
                      alt={item.product_title}
                      className="w-12 h-12 object-contain bg-slate-50 rounded-xl p-1 border border-slate-100 flex-shrink-0"
                    />
                  ) : (
                    <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center text-slate-400 text-xs font-bold flex-shrink-0">
                      Item
                    </div>
                  )}

                  <div className="min-w-0">
                    <Link
                      to={`/products/${item.product_id}`}
                      className="text-sm font-bold text-slate-900 hover:text-brand-600 truncate block"
                    >
                      {item.product_title || `Product #${item.product_id}`}
                    </Link>
                    <div className="flex items-center space-x-2 text-xs text-slate-400 mt-0.5">
                      <span>{item.category || 'General'}</span>
                      {item.price && <span>• ${parseFloat(item.price).toFixed(2)}</span>}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-4 self-end sm:self-auto">
                  {/* Rating display if present */}
                  {item.rating !== null && item.rating !== undefined && (
                    <div className="flex items-center space-x-1 text-amber-500 font-bold text-xs bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200">
                      <Star className="w-3.5 h-3.5 fill-amber-400" />
                      <span>{parseFloat(item.rating).toFixed(1)} Stars</span>
                    </div>
                  )}

                  {/* Interaction tag */}
                  <span
                    className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${config.bg}`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span className="capitalize">{config.label}</span>
                  </span>

                  {/* Timestamp */}
                  <span className="text-[11px] text-slate-400 whitespace-nowrap">
                    {item.timestamp ? new Date(item.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'Recent'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default History;
