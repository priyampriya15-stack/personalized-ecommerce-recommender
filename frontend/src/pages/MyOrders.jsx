import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Package,
  Clock,
  XCircle,
  AlertCircle,
  ImageOff,
  ShoppingBag,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  FileText,
  Calendar,
  Hash,
  DollarSign,
} from 'lucide-react';
import orderService from '../services/orderService';
import Toast from '../components/Toast';

export const MyOrders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState(null);
  const [confirmCancelId, setConfirmCancelId] = useState(null);
  const [expandedOrderId, setExpandedOrderId] = useState(null);
  const [imgErrors, setImgErrors] = useState({});
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const showToast = (message, type = 'success') => setToast({ message, type });

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const res = await orderService.getUserOrders();
      if (res && res.data) {
        setOrders(res.data);
      }
    } catch (err) {
      showToast(err.message || 'Failed to fetch orders.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const handleCancelOrder = async (orderId) => {
    try {
      setCancellingId(orderId);
      const res = await orderService.cancelOrder(orderId);
      if (res && res.data) {
        setOrders((prev) =>
          prev.map((o) => (o.id === orderId ? { ...o, status: 'CANCELLED', updated_at: new Date().toISOString() } : o))
        );
        showToast(`Order #${orderId} has been cancelled.`, 'info');
      }
    } catch (err) {
      showToast(err.message || 'Failed to cancel order.', 'error');
    } finally {
      setCancellingId(null);
      setConfirmCancelId(null);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PENDING':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'CONFIRMED':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'CANCELLED':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'COMPLETED':
      case 'DELIVERED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const toggleExpand = (orderId) => {
    setExpandedOrderId((prev) => (prev === orderId ? null : orderId));
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2 text-brand-600 mb-1">
            <Package className="w-5 h-5 text-brand-500" />
            <span className="text-xs font-bold uppercase tracking-wider">Purchase History</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            My Orders
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real orders placed and recorded in SQLite database.
          </p>
        </div>

        <Link
          to="/products"
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
        >
          <span>Catalog Products</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* Loading Skeleton */}
      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[1, 2].map((i) => (
            <div key={i} className="h-44 bg-slate-100 rounded-3xl border border-slate-200" />
          ))}
        </div>
      ) : orders.length === 0 ? (
        /* Honest Empty State */
        <div className="max-w-md mx-auto text-center py-16 space-y-4">
          <div className="w-16 h-16 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto">
            <ShoppingBag className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-slate-800">No orders yet.</h2>
            <p className="text-xs text-slate-500 leading-relaxed">
              You have not placed any orders yet. Discover items from our verified Amazon catalog or check your personalized recommendation stream.
            </p>
          </div>
          <Link
            to="/products"
            className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 text-white text-xs font-bold rounded-xl shadow-md hover:bg-brand-700 transition-colors"
          >
            <span>Start Shopping</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        /* Real Orders List */
        <div className="space-y-6">
          {orders.map((order) => {
            const isPending = order.status === 'PENDING';
            const isCancelling = cancellingId === order.id;
            const isConfirming = confirmCancelId === order.id;
            const isExpanded = expandedOrderId === order.id;

            return (
              <div
                key={order.id}
                className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow"
              >
                {/* Order Top Summary Bar */}
                <div className="p-4 sm:p-6 bg-slate-50/80 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-4">
                  <div className="flex flex-wrap items-center gap-4 text-xs">
                    <div>
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Order ID</span>
                      <span className="font-mono font-bold text-slate-800">#{order.id}</span>
                    </div>

                    <div className="border-l border-slate-200 pl-4">
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Date Placed</span>
                      <span className="text-slate-700 flex items-center space-x-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>
                          {order.created_at
                            ? new Date(order.created_at).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                              })
                            : 'N/A'}
                        </span>
                      </span>
                    </div>

                    <div className="border-l border-slate-200 pl-4">
                      <span className="text-slate-400 block text-[10px] uppercase font-bold">Total Amount</span>
                      <span className="font-mono font-bold text-slate-900 text-sm">
                        ${order.total_amount?.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {/* Status Badge & Actions */}
                  <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                    <span
                      className={`text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full border ${getStatusBadge(
                        order.status
                      )}`}
                    >
                      {order.status}
                    </span>

                    {/* Order Details Toggle */}
                    <button
                      type="button"
                      onClick={() => toggleExpand(order.id)}
                      className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-100 text-xs font-semibold transition-colors"
                      title="View Order Details"
                    >
                      <FileText className="w-3.5 h-3.5 text-slate-400" />
                      <span>{isExpanded ? 'Hide Details' : 'Order Details'}</span>
                      {isExpanded ? (
                        <ChevronUp className="w-3 h-3 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-3 h-3 text-slate-400" />
                      )}
                    </button>

                    {/* Cancel Order Action (Only for PENDING status) */}
                    {isPending && (
                      <div>
                        {isConfirming ? (
                          <div className="flex items-center space-x-2 bg-rose-50 p-1.5 rounded-xl border border-rose-200">
                            <span className="text-[11px] font-semibold text-rose-700 px-1">
                              Cancel this order?
                            </span>
                            <button
                              type="button"
                              disabled={isCancelling}
                              onClick={() => handleCancelOrder(order.id)}
                              className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
                            >
                              {isCancelling ? 'Cancelling...' : 'Yes, Cancel'}
                            </button>
                            <button
                              type="button"
                              onClick={() => setConfirmCancelId(null)}
                              className="px-2 py-1 bg-white hover:bg-slate-100 text-slate-600 rounded-lg text-xs font-semibold border border-slate-200"
                            >
                              No
                            </button>
                          </div>
                        ) : (
                          <button
                            type="button"
                            onClick={() => setConfirmCancelId(order.id)}
                            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-rose-200 text-rose-600 hover:bg-rose-50 text-xs font-semibold transition-colors"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Cancel Order</span>
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Line Items List */}
                <div className="p-4 sm:p-6 divide-y divide-slate-100">
                  {order.items?.map((item) => (
                    <div key={item.id} className="py-3.5 flex items-center justify-between gap-4">
                      <div className="flex items-center space-x-3.5 min-w-0">
                        <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center flex-shrink-0 p-1">
                          {item.image_url && !imgErrors[item.product_id] ? (
                            <img
                              src={item.image_url}
                              alt={item.title}
                              onError={() => setImgErrors((prev) => ({ ...prev, [item.product_id]: true }))}
                              className="w-full h-full object-contain mix-blend-multiply"
                            />
                          ) : (
                            <ImageOff className="w-5 h-5 text-slate-300" />
                          )}
                        </div>

                        <div className="min-w-0">
                          <Link
                            to={`/products/${item.product_id}`}
                            className="text-xs sm:text-sm font-bold text-slate-800 hover:text-brand-600 truncate block transition-colors"
                            title={item.title}
                          >
                            {item.title || `Catalog Product #${item.product_id}`}
                          </Link>
                          <p className="text-[11px] text-slate-400 mt-0.5">
                            Category: {item.category || 'General'}
                          </p>
                          <p className="text-[11px] text-slate-500 font-mono mt-0.5">
                            Quantity: {item.quantity} × ${item.unit_price?.toFixed(2)}
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

                {/* Expandable Order Details View */}
                {isExpanded && (
                  <div className="p-4 sm:p-6 bg-slate-50/50 border-t border-slate-100 text-xs text-slate-600 space-y-3">
                    <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px] flex items-center space-x-1.5">
                      <FileText className="w-3.5 h-3.5 text-brand-600" />
                      <span>Order Breakdown & Audit Telemetry</span>
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 bg-white p-4 rounded-2xl border border-slate-200/80">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Order ID</span>
                        <span className="font-mono font-bold text-slate-800">#{order.id}</span>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Status</span>
                        <span className="font-bold text-slate-800">{order.status}</span>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Created At</span>
                        <span className="font-mono text-slate-700">{order.created_at || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Total Items</span>
                        <span className="font-bold text-slate-800">{order.items_count || order.items?.length || 0}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MyOrders;
