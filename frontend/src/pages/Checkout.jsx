import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { ShoppingBag, ArrowLeft, CheckCircle2, ShieldCheck, Truck, CreditCard, ImageOff } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import orderService from '../services/orderService';
import Toast from '../components/Toast';

export const Checkout = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, updateCartCount } = useAuth();

  const productId = searchParams.get('productId');
  const initialQty = parseInt(searchParams.get('quantity') || '1', 10);
  const isBuyNow = !!productId;

  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [completedOrder, setCompletedOrder] = useState(null);
  const [imgErrors, setImgErrors] = useState({});
  const [toast, setToast] = useState({ message: '', type: 'success' });

  // Shipping Form State
  const [shippingAddress, setShippingAddress] = useState({
    fullName: user?.name || '',
    address: '123 Academic Research Way',
    city: 'San Diego',
    state: 'CA',
    postalCode: '92093',
    paymentMethod: 'cod',
  });

  const showToast = (message, type = 'success') => setToast({ message, type });

  // Fetch real order quote computed by Flask from SQLite
  useEffect(() => {
    let isMounted = true;

    const fetchQuote = async () => {
      try {
        setLoading(true);
        setError(null);

        const payload = isBuyNow
          ? { product_id: parseInt(productId, 10), quantity: initialQty }
          : { source: 'cart' };

        const res = await orderService.getOrderQuote(payload);
        if (isMounted && res && res.data) {
          setQuote(res.data);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to calculate verified checkout pricing.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchQuote();

    return () => {
      isMounted = false;
    };
  }, [productId, initialQty, isBuyNow]);

  const handleConfirmOrder = async (e) => {
    e.preventDefault();
    if (submitting || !quote) return;

    try {
      setSubmitting(true);
      setError(null);

      const payload = isBuyNow
        ? { product_id: parseInt(productId, 10), quantity: initialQty }
        : { source: 'cart' };

      const res = await orderService.createOrder(payload);
      if (res && res.data) {
        setCompletedOrder(res.data);
        if (!isBuyNow) {
          updateCartCount(0);
        }
        showToast('Order confirmed and recorded in database!', 'success');
      }
    } catch (err) {
      setError(err.message || 'Failed to place order.');
      showToast(err.message || 'Order failed.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-slate-200 rounded w-48" />
          <div className="h-64 bg-slate-100 rounded-3xl border border-slate-200" />
        </div>
      </div>
    );
  }

  // Order Confirmed State
  if (completedOrder) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center space-y-6 animate-fade-in">
        <div className="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mx-auto border border-emerald-200 shadow-sm">
          <CheckCircle2 className="w-10 h-10" />
        </div>

        <div className="space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
            Order Confirmed #{completedOrder.id}
          </span>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">
            Thank You for Your Order!
          </h1>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Your order has been recorded into the SQLite database. Total amount verified server-side:
          </p>
          <p className="text-3xl font-extrabold text-brand-700 font-mono">
            ${completedOrder.total_amount?.toFixed(2)}
          </p>
        </div>

        <div className="p-6 bg-white rounded-2xl border border-slate-200 text-left space-y-3 shadow-sm">
          <div className="flex justify-between text-xs text-slate-500 pb-2 border-b border-slate-100">
            <span>Status: <strong className="text-slate-800">{completedOrder.status}</strong></span>
            <span>Items: <strong className="text-slate-800">{completedOrder.items_count}</strong></span>
          </div>
          <div className="divide-y divide-slate-100">
            {completedOrder.items?.map((item) => (
              <div key={item.id} className="py-2 flex justify-between text-xs">
                <span className="font-medium text-slate-800 truncate max-w-[280px]">
                  {item.quantity} × {item.title || `Product #${item.product_id}`}
                </span>
                <span className="font-mono text-slate-600">${item.subtotal?.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
          <Link
            to="/orders"
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-sm shadow-md transition-all text-center"
          >
            View My Orders
          </Link>
          <Link
            to="/products"
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-sm transition-all text-center"
          >
            Continue Shopping
          </Link>
        </div>
      </div>
    );
  }

  // Error / Empty State
  if (error || !quote || !quote.items || quote.items.length === 0) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-6">
        <div className="w-16 h-16 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto">
          <ShoppingBag className="w-8 h-8" />
        </div>
        <div className="space-y-1">
          <h2 className="text-xl font-bold text-slate-800">No Items to Checkout</h2>
          <p className="text-xs text-slate-500">
            {error || 'Your shopping cart is currently empty or no product was selected.'}
          </p>
        </div>
        <Link
          to="/products"
          className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 text-white rounded-xl text-xs font-bold hover:bg-brand-700 transition-colors shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Browse Product Catalog</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div>
          <Link
            to={isBuyNow ? `/products/${productId}` : '/profile'}
            className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-brand-600 transition-colors mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{isBuyNow ? 'Back to Product' : 'Back to Cart'}</span>
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Checkout & Order Confirmation
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Prices verified directly from SQLite database. Complete your order below.
          </p>
        </div>
        <div className="hidden sm:flex items-center space-x-1 text-emerald-600 text-xs font-bold bg-emerald-50 px-3 py-1.5 rounded-full border border-emerald-200">
          <ShieldCheck className="w-4 h-4" />
          <span>Server-Side Price Verified</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Order Items & Delivery Details */}
        <div className="lg:col-span-7 space-y-6">
          {/* Items Review Card */}
          <div className="bg-white rounded-3xl border border-slate-200 p-4 sm:p-8 shadow-sm space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 pb-2 border-b border-slate-100 flex items-center justify-between">
              <span>Order Items ({quote.items_count})</span>
              <span className="text-xs font-mono font-semibold text-brand-600">
                {isBuyNow ? 'Buy Now Direct' : 'Shopping Cart'}
              </span>
            </h2>

            <div className="divide-y divide-slate-100">
              {quote.items.map((item) => (
                <div key={item.product_id} className="py-4 flex items-center justify-between gap-4">
                  <div className="flex items-center space-x-3 min-w-0">
                    <div className="w-14 h-14 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center flex-shrink-0 p-1">
                      {item.image_url && !imgErrors[item.product_id] ? (
                        <img
                          src={item.image_url}
                          alt={item.title}
                          onError={() => setImgErrors((prev) => ({ ...prev, [item.product_id]: true }))}
                          className="w-full h-full object-contain mix-blend-multiply"
                        />
                      ) : (
                        <ImageOff className="w-6 h-6 text-slate-300" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-slate-800 truncate" title={item.title}>
                        {item.title}
                      </p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Category: {item.category}
                      </p>
                      <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                        ${item.unit_price?.toFixed(2)} × {item.quantity}
                      </p>
                    </div>
                  </div>

                  <div className="text-right flex-shrink-0">
                    <span className="text-sm font-bold text-slate-900 font-mono">
                      ${item.subtotal?.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Delivery & Payment Form */}
          <div className="bg-white rounded-3xl border border-slate-200 p-4 sm:p-8 shadow-sm space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 pb-2 border-b border-slate-100 flex items-center space-x-2">
              <Truck className="w-4 h-4 text-brand-600" />
              <span>Shipping Information</span>
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Recipient Name
                </label>
                <input
                  type="text"
                  required
                  value={shippingAddress.fullName}
                  onChange={(e) => setShippingAddress({ ...shippingAddress, fullName: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:border-brand-500 outline-none transition-all"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Street Address
                </label>
                <input
                  type="text"
                  required
                  value={shippingAddress.address}
                  onChange={(e) => setShippingAddress({ ...shippingAddress, address: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:border-brand-500 outline-none transition-all"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  City / State
                </label>
                <input
                  type="text"
                  required
                  value={`${shippingAddress.city}, ${shippingAddress.state}`}
                  onChange={(e) => setShippingAddress({ ...shippingAddress, city: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:border-brand-500 outline-none transition-all"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">
                  Payment Method
                </label>
                <select
                  value={shippingAddress.paymentMethod}
                  onChange={(e) => setShippingAddress({ ...shippingAddress, paymentMethod: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:bg-white focus:border-brand-500 outline-none transition-all"
                >
                  <option value="cod">Cash on Delivery (Standard)</option>
                  <option value="card">Research Academic Card (Simulated)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Server Price Calculation & Order Button */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white rounded-3xl border border-slate-200 p-4 sm:p-8 shadow-sm space-y-6 sticky top-24">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 pb-2 border-b border-slate-100 flex items-center space-x-2">
              <CreditCard className="w-4 h-4 text-brand-600" />
              <span>Order Summary</span>
            </h2>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between text-slate-500">
                <span>Items Subtotal:</span>
                <span className="font-mono font-semibold text-slate-800">
                  ${quote.total_amount?.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-slate-500">
                <span>Shipping & Handling:</span>
                <span className="font-mono text-emerald-600 font-semibold">FREE</span>
              </div>
              <div className="flex justify-between text-slate-500">
                <span>Estimated Tax:</span>
                <span className="font-mono text-slate-800">$0.00</span>
              </div>

              <div className="pt-3 border-t border-slate-100 flex justify-between items-center text-sm font-extrabold text-slate-900">
                <span>Order Total:</span>
                <span className="text-2xl text-brand-700 font-mono">
                  ${quote.total_amount?.toFixed(2)}
                </span>
              </div>
            </div>

            <button
              id="confirm-order-button"
              type="button"
              onClick={handleConfirmOrder}
              disabled={submitting}
              className="w-full py-4 px-6 bg-brand-600 hover:bg-brand-700 active:scale-95 text-white font-bold rounded-xl text-sm shadow-lg shadow-brand-500/25 transition-all disabled:opacity-50 flex items-center justify-center space-x-2"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Recording Order in SQLite...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Confirm & Place Order</span>
                </>
              )}
            </button>

            <p className="text-[11px] text-slate-400 text-center leading-relaxed">
              By confirming, this order will be saved to the database. All amounts are computed server-side from catalog data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;
