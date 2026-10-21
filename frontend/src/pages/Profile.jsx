import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { User, Mail, Calendar, Shield, ShoppingBag, Trash2, CheckCircle2, Sparkles, CreditCard } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import cartService from '../services/cartService';
import interactionService from '../services/interactionService';
import Toast from '../components/Toast';

export const Profile = () => {
  const { user, refreshUser, updateCartCount } = useAuth();
  const [cart, setCart] = useState(null);
  const [loadingCart, setLoadingCart] = useState(true);
  const [checkingOut, setCheckingOut] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState(user?.preferred_categories || []);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const allCategories = ['All Beauty', 'Appliances', 'Digital Music'];

  const showToast = (message, type = 'success') => setToast({ message, type });

  const fetchCart = async () => {
    try {
      setLoadingCart(true);
      const res = await cartService.getCart();
      if (res && res.data) {
        setCart(res.data);
        updateCartCount(res.data.total_items || 0);
      }
    } catch (err) {
      console.error('Failed to load cart:', err);
    } finally {
      setLoadingCart(false);
    }
  };

  useEffect(() => {
    fetchCart();
  }, []);

  useEffect(() => {
    if (user?.preferred_categories) {
      setSelectedCategories(user.preferred_categories);
    }
  }, [user]);

  const toggleCategory = (cat) => {
    if (selectedCategories.includes(cat)) {
      setSelectedCategories(selectedCategories.filter((c) => c !== cat));
    } else {
      setSelectedCategories([...selectedCategories, cat]);
    }
  };

  const handleSavePreferences = async () => {
    try {
      setSavingPrefs(true);
      await interactionService.updatePreferences(selectedCategories);
      await refreshUser();
      showToast('Preferences updated! Recommender tuned.', 'success');
    } catch (err) {
      showToast(err.message || 'Failed to save preferences.', 'error');
    } finally {
      setSavingPrefs(false);
    }
  };

  const handleRemoveCartItem = async (productId) => {
    try {
      await cartService.removeFromCart(productId);
      showToast('Item removed from cart.', 'info');
      await fetchCart();
    } catch (err) {
      showToast(err.message || 'Failed to remove item.', 'error');
    }
  };

  const handleCheckout = async () => {
    try {
      setCheckingOut(true);
      const res = await cartService.checkout();
      if (res && res.data) {
        showToast(`Purchase complete! ${res.data.purchased_items_count} item(s) logged to interaction history.`, 'success');
        updateCartCount(0);
        await fetchCart();
        await refreshUser();
      }
    } catch (err) {
      showToast(err.message || 'Checkout failed.', 'error');
    } finally {
      setCheckingOut(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      <div className="pb-4 border-b border-slate-200">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          User Account & Active Cart
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Manage your account profile, recommendation affinities, and shopping basket
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: User Profile & Preferences */}
        <div className="space-y-6">
          {/* Profile Card */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center space-x-3 pb-4 border-b border-slate-100">
              <div className="w-12 h-12 rounded-2xl bg-brand-600 text-white flex items-center justify-center font-bold text-lg shadow-md shadow-brand-500/25">
                {user?.name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900">{user?.name}</h3>
                <span className="inline-block text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                  Role: {user?.role}
                </span>
              </div>
            </div>

            <div className="space-y-2 text-xs text-slate-600">
              <div className="flex items-center space-x-2">
                <Mail className="w-4 h-4 text-slate-400" />
                <span className="truncate">{user?.email}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-slate-400" />
                <span>Member since {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '2026'}</span>
              </div>
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-slate-400" />
                <span>Account Status: Active & Verified</span>
              </div>
            </div>
          </div>

          {/* Preferences Card */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <div className="flex items-center space-x-2 pb-2 border-b border-slate-100 text-slate-900 font-bold text-sm">
              <Sparkles className="w-4 h-4 text-brand-600" />
              <span>Category Preferences</span>
            </div>
            <p className="text-xs text-slate-500">
              Select the categories you are most interested in. Our Content-Based and Hybrid models use this to curate your recommendations.
            </p>

            <div className="flex flex-wrap gap-2">
              {allCategories.map((cat) => {
                const isSelected = selectedCategories.includes(cat);
                return (
                  <button
                    key={cat}
                    onClick={() => toggleCategory(cat)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                      isSelected
                        ? 'bg-brand-600 text-white shadow-sm'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {isSelected && <CheckCircle2 className="w-3.5 h-3.5" />}
                    <span>{cat}</span>
                  </button>
                );
              })}
            </div>

            <button
              onClick={handleSavePreferences}
              disabled={savingPrefs}
              className="w-full py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50"
            >
              {savingPrefs ? 'Updating...' : 'Save Preferences'}
            </button>
          </div>
        </div>

        {/* Right Column: Shopping Cart */}
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 bg-brand-50 text-brand-600 rounded-xl">
                <ShoppingBag className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold text-slate-900">Active Shopping Cart</h2>
            </div>
            <span className="text-xs font-semibold text-slate-500">
              {cart?.items?.length || 0} line item(s)
            </span>
          </div>

          {loadingCart ? (
            <div className="space-y-4 animate-pulse">
              <div className="h-16 bg-slate-100 rounded-2xl w-full" />
              <div className="h-16 bg-slate-100 rounded-2xl w-full" />
            </div>
          ) : !cart || !cart.items || cart.items.length === 0 ? (
            <div className="py-12 text-center text-slate-400">
              <ShoppingBag className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm font-semibold text-slate-700 mb-1">Your cart is currently empty</p>
              <p className="text-xs text-slate-400 mb-4">Add products from the catalog to test real checkout workflows.</p>
              <Link
                to="/products"
                className="inline-flex items-center px-4 py-2 bg-brand-600 text-white rounded-xl text-xs font-semibold hover:bg-brand-700"
              >
                Browse Catalog
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="divide-y divide-slate-100">
                {cart.items.map((item) => (
                  <div key={item.id} className="py-4 flex items-center justify-between gap-4">
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      {item.product?.image_url ? (
                        <img
                          src={item.product.image_url}
                          alt={item.product.title}
                          className="w-14 h-14 object-contain rounded-lg bg-slate-50 p-1 flex-shrink-0"
                        />
                      ) : (
                        <div className="w-14 h-14 bg-slate-100 rounded-lg flex items-center justify-center flex-shrink-0 text-slate-400 text-xs font-bold">
                          Item
                        </div>
                      )}
                      <div className="min-w-0">
                        <Link
                          to={`/products/${item.product_id}`}
                          className="text-xs font-bold text-slate-900 hover:text-brand-600 truncate block"
                        >
                          {item.product?.title || `Product #${item.product_id}`}
                        </Link>
                        <p className="text-[11px] text-slate-400">
                          Qty: {item.quantity} × ${item.product?.price?.toFixed(2) || '0.00'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-bold text-slate-900">
                        ${item.subtotal?.toFixed(2)}
                      </span>
                      <button
                        onClick={() => handleRemoveCartItem(item.product_id)}
                        className="p-1.5 text-slate-400 hover:text-rose-500 rounded-lg hover:bg-rose-50 transition-colors"
                        title="Remove from cart"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Cart Summary & Checkout */}
              <div className="pt-6 border-t border-slate-200 space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500">Total Items:</span>
                  <span className="font-bold text-slate-800">{cart.total_items}</span>
                </div>
                <div className="flex items-center justify-between text-base font-extrabold text-slate-900">
                  <span>Grand Total:</span>
                  <span className="text-2xl text-brand-700">${cart.total_price?.toFixed(2)}</span>
                </div>

                <Link
                  to="/checkout"
                  className="w-full py-3.5 px-6 bg-brand-600 hover:bg-brand-700 active:scale-95 text-white font-bold rounded-xl text-sm shadow-lg shadow-brand-500/25 transition-all flex items-center justify-center space-x-2 text-center"
                >
                  <CreditCard className="w-4 h-4" />
                  <span>Proceed to Checkout</span>
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
