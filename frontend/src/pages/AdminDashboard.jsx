import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Users,
  Package,
  Activity,
  Sliders,
  Cpu,
  BarChart3,
  TrendingUp,
  RefreshCw,
  Sparkles,
  Info,
  CheckCircle2,
  AlertCircle,
  Database,
  Server,
  Calendar,
  Star,
  Eye,
  ThumbsUp,
  ShoppingCart,
  ShoppingBag,
  Award,
  ChevronRight,
  Clock,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
  AreaChart,
  Area,
  CartesianGrid,
} from 'recharts';
import { useAuth } from '../hooks/useAuth';
import adminService from '../services/adminService';
import ErrorMessage from '../components/ErrorMessage';
import Toast from '../components/Toast';

export const AdminDashboard = () => {
  const { user, isAdmin } = useAuth();

  const [analytics, setAnalytics] = useState(null);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [alphaVal, setAlphaVal] = useState(0.25);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'models' | 'tables'
  const [loading, setLoading] = useState(true);
  const [savingAlpha, setSavingAlpha] = useState(false);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success' });
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const showToast = (message, type = 'success') => setToast({ message, type });

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [anRes, mmRes] = await Promise.all([
        adminService.getAnalytics(),
        adminService.getModelMetrics(),
      ]);

      if (anRes && anRes.data) {
        setAnalytics(anRes.data);
        if (anRes.data.overview?.current_hybrid_alpha !== undefined) {
          setAlphaVal(anRes.data.overview.current_hybrid_alpha);
        }
      }
      if (mmRes && mmRes.data) {
        setModelMetrics(mmRes.data);
      }
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err.message || 'Failed to fetch admin telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      fetchDashboardData();
    }
  }, [isAdmin]);

  const handleUpdateAlpha = async (e) => {
    e.preventDefault();
    if (alphaVal < 0 || alphaVal > 1) {
      showToast('Alpha parameter must be between 0.0 and 1.0', 'error');
      return;
    }

    try {
      setSavingAlpha(true);
      const res = await adminService.updateRecommendationSettings(alphaVal);
      if (res && res.data) {
        showToast(
          `Hybrid α successfully updated to ${res.data.current_hybrid_alpha} (${Math.round(
            res.data.collaborative_weight * 100
          )}% CF / ${Math.round(res.data.content_weight * 100)}% CB). Live engine re-weighted!`,
          'success'
        );
        await fetchDashboardData();
      }
    } catch (err) {
      showToast(err.message || 'Failed to update hybrid alpha parameter.', 'error');
    } finally {
      setSavingAlpha(false);
    }
  };

  if (!isAdmin) {
    return (
      <div className="max-w-md mx-auto py-24 text-center px-4">
        <div className="w-16 h-16 rounded-3xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-4 border border-rose-200">
          <ShieldCheck className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Admin Access Required</h2>
        <p className="text-sm text-slate-500 mb-6">
          This portal is strictly restricted to authenticated platform administrators with the admin role in SQLite.
        </p>
      </div>
    );
  }

  // Real Database Formatted Visual Data
  const categoryData = analytics?.categories_detailed
    ? analytics.categories_detailed.map((c) => ({
        name: c.category,
        products: c.product_count,
        interactions: c.interaction_count,
        avgRating: c.avg_rating,
      }))
    : analytics?.category_statistics
    ? Object.entries(analytics.category_statistics).map(([name, count]) => ({
        name,
        products: count,
      }))
    : [];

  const interactionColors = {
    rating: '#6366f1',
    like: '#ec4899',
    view: '#14b8a6',
    cart: '#f59e0b',
    purchase: '#10b981',
  };

  const interactionData = analytics?.interaction_breakdown
    ? Object.entries(analytics.interaction_breakdown).map(([name, value]) => ({
        name: name.toUpperCase(),
        value,
        color: interactionColors[name.toLowerCase()] || '#94a3b8',
      }))
    : [];

  const algoColors = {
    hybrid: '#8b5cf6',
    content_based: '#06b6d4',
    collaborative: '#3b82f6',
    popularity: '#f97316',
  };

  const algorithmData = analytics?.algorithm_usage
    ? Object.entries(analytics.algorithm_usage).map(([algo, count]) => ({
        name: algo.replace('_', ' ').toUpperCase(),
        value: count,
        color: algoColors[algo.toLowerCase()] || '#64748b',
      }))
    : [];

  // Model comparison metrics data for K=10 grouped bar chart
  const modelComparisonChartData = modelMetrics?.k10_models
    ? modelMetrics.k10_models.map((m) => ({
        model: m.Model.replace(' (alpha=0.5)', ''),
        recallPct: Number((parseFloat(m['Recall@K'] || 0) * 100).toFixed(2)),
        precisionPct: Number((parseFloat(m['Precision@K'] || 0) * 100).toFixed(2)),
        ndcg: Number(parseFloat(m['NDCG@K'] || 0).toFixed(4)),
        diversity: Number(parseFloat(m['Diversity@K'] || 0).toFixed(4)),
      }))
    : [];

  const timelineData = analytics?.interactions_timeline || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      {/* Header Banner */}
      <div className="bg-white rounded-3xl border border-slate-200/80 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center space-x-2 text-indigo-600 mb-1.5">
            <ShieldCheck className="w-5 h-5" />
            <span className="text-xs font-bold uppercase tracking-wider">Platform Administration</span>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse" />
              Live Real SQLite Data
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Admin Telemetry & Model Control
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Real platform analytics from SQLite, empirical Phase 3 model evaluation benchmarks, and live Hybrid recommender weight tuning.
          </p>
          {lastRefreshed && (
            <p className="text-[11px] text-slate-400 mt-2 flex items-center space-x-1">
              <Clock className="w-3 h-3 inline" />
              <span>Last synced with database: {lastRefreshed}</span>
            </p>
          )}
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchDashboardData}
            disabled={loading}
            className="inline-flex items-center space-x-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 active:scale-95 text-white rounded-xl text-xs font-bold shadow-md shadow-slate-900/10 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh SQLite Telemetry</span>
          </button>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex border-b border-slate-200 space-x-3 sm:space-x-6 text-xs sm:text-sm font-semibold overflow-x-auto no-scrollbar whitespace-nowrap pb-1">
        <button
          onClick={() => setActiveTab('overview')}
          className={`pb-3 transition-colors flex items-center space-x-1.5 border-b-2 flex-shrink-0 ${
            activeTab === 'overview'
              ? 'border-brand-600 text-brand-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Platform Overview</span>
        </button>
        <button
          onClick={() => setActiveTab('models')}
          className={`pb-3 transition-colors flex items-center space-x-1.5 border-b-2 flex-shrink-0 ${
            activeTab === 'models'
              ? 'border-brand-600 text-brand-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Cpu className="w-4 h-4" />
          <span>Model Evaluation (Phase 3)</span>
        </button>
        <button
          onClick={() => setActiveTab('tables')}
          className={`pb-3 transition-colors flex items-center space-x-1.5 border-b-2 flex-shrink-0 ${
            activeTab === 'tables'
              ? 'border-brand-600 text-brand-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>Activity & Catalog Tables</span>
        </button>
      </div>

      {error ? (
        <ErrorMessage message={error} onRetry={fetchDashboardData} />
      ) : loading && !analytics ? (
        /* Loading Skeletons */
        <div className="space-y-6 animate-pulse">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-28 bg-slate-100 rounded-3xl" />
            ))}
          </div>
          <div className="h-80 bg-slate-100 rounded-3xl" />
          <div className="h-64 bg-slate-100 rounded-3xl" />
        </div>
      ) : (
        <>
          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="space-y-8 animate-fade-in">
              {/* Top KPI Cards (Real SQLite Counts) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                {/* Users KPI */}
                <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-sm flex items-center justify-between">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                      Total Registered Users
                    </span>
                    <span className="text-2xl font-black text-slate-900">
                      {analytics?.overview?.total_users?.toLocaleString() || 0}
                    </span>
                    <span className="text-[11px] text-emerald-600 block mt-1 font-semibold">
                      {analytics?.overview?.active_users || 0} with interactions
                    </span>
                  </div>
                  <div className="p-3 bg-teal-50 text-teal-600 rounded-2xl border border-teal-100">
                    <Users className="w-5 h-5" />
                  </div>
                </div>

                {/* Catalog Products KPI */}
                <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-sm flex items-center justify-between">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                      Catalog Products
                    </span>
                    <span className="text-2xl font-black text-slate-900">
                      {analytics?.overview?.total_products?.toLocaleString() || 0}
                    </span>
                    <span className="text-[11px] text-indigo-600 block mt-1 font-semibold">
                      Avg Rating: {analytics?.overview?.catalog_avg_rating || '0.0'} ★
                    </span>
                  </div>
                  <div className="p-3 bg-indigo-50 text-indigo-600 rounded-2xl border border-indigo-100">
                    <Package className="w-5 h-5" />
                  </div>
                </div>

                {/* Total Interactions KPI */}
                <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-sm flex items-center justify-between">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                      Recorded Interactions
                    </span>
                    <span className="text-2xl font-black text-slate-900">
                      {analytics?.overview?.total_interactions?.toLocaleString() || 0}
                    </span>
                    <span className="text-[11px] text-amber-600 block mt-1 font-semibold">
                      {analytics?.overview?.interacted_products_count || 0} unique items
                    </span>
                  </div>
                  <div className="p-3 bg-amber-50 text-amber-600 rounded-2xl border border-amber-100">
                    <Activity className="w-5 h-5" />
                  </div>
                </div>

                {/* Hybrid Alpha KPI */}
                <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-sm flex items-center justify-between">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                      Current Hybrid Alpha (α)
                    </span>
                    <span className="text-2xl font-black text-brand-700">
                      {Number(analytics?.overview?.current_hybrid_alpha || 0.25).toFixed(2)}
                    </span>
                    <span className="text-[11px] text-slate-500 block mt-1 font-medium">
                      {Math.round((analytics?.overview?.current_hybrid_alpha || 0.25) * 100)}% CF / {Math.round((1 - (analytics?.overview?.current_hybrid_alpha || 0.25)) * 100)}% CB
                    </span>
                  </div>
                  <div className="p-3 bg-brand-50 text-brand-600 rounded-2xl border border-brand-100">
                    <Sliders className="w-5 h-5" />
                  </div>
                </div>
              </div>

              {/* Dynamic Hyperparameter Tuning Section */}
              <div className="bg-gradient-to-br from-white to-slate-50 rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/80">
                  <div className="flex items-center space-x-2 text-slate-900 font-extrabold text-base">
                    <Sliders className="w-5 h-5 text-brand-600" />
                    <span>Live Recommendation Engine Weight Adjustment</span>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-brand-50 text-brand-700 border border-brand-200">
                    Active Formula: Score = α · CF + (1 - α) · CB
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed max-w-4xl">
                  Adjusting the <code className="bg-slate-200/70 px-1.5 py-0.5 rounded font-mono text-brand-800 font-bold">α</code> parameter
                  dynamically re-weights the candidate scoring balance between Truncated SVD Collaborative Filtering and TF-IDF Content-Based Filtering.
                  Phase 3 empirical offline evaluation over <strong className="text-slate-900">2,064 test users</strong> verified the optimum at <strong className="text-brand-700">α = 0.25</strong> (Recall@10 = 20.99%, NDCG@10 = 0.1420).
                </p>

                <form onSubmit={handleUpdateAlpha} className="space-y-4 pt-2">
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                    <div className="md:col-span-8 space-y-2">
                      <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                        <span className="text-blue-600">Collaborative Factor (α): {Math.round(alphaVal * 100)}%</span>
                        <span className="text-teal-600">Content Factor (1 - α): {Math.round((1 - alphaVal) * 100)}%</span>
                      </div>
                      <input
                        type="range"
                        min="0.0"
                        max="1.0"
                        step="0.05"
                        value={alphaVal}
                        onChange={(e) => setAlphaVal(parseFloat(e.target.value))}
                        className="w-full h-2.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-600"
                      />
                      <div className="flex flex-wrap justify-between gap-1 text-[9px] sm:text-[10px] text-slate-400 font-mono">
                        <span>0.00 <span className="hidden sm:inline">(Pure CB)</span></span>
                        <span className="text-brand-600 font-bold">0.25 (Optimum)</span>
                        <span>0.50</span>
                        <span>1.00 <span className="hidden sm:inline">(Pure CF)</span></span>
                      </div>
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-[11px] font-semibold text-slate-500 mb-1">
                        Exact Value
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.01"
                        value={alphaVal}
                        onChange={(e) => setAlphaVal(Math.max(0, Math.min(1, parseFloat(e.target.value) || 0)))}
                        className="w-full p-2.5 bg-white border border-slate-300 rounded-xl text-center font-mono font-bold text-sm text-slate-800 shadow-inner"
                      />
                    </div>

                    <div className="md:col-span-2 flex items-end">
                      <button
                        type="submit"
                        disabled={savingAlpha}
                        className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 active:scale-95 text-white font-bold rounded-xl text-xs shadow-md shadow-brand-500/25 transition-all disabled:opacity-50"
                      >
                        {savingAlpha ? 'Saving...' : 'Save Live α'}
                      </button>
                    </div>
                  </div>
                </form>
              </div>

              {/* Recharts Analytics Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* 1. Catalog Products by Category */}
                <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
                      <BarChart3 className="w-4 h-4 text-brand-600" />
                      <span>Product Distribution by Category</span>
                    </div>
                    <span className="text-[11px] text-slate-400 font-medium">8,337 Products</span>
                  </div>

                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={categoryData} margin={{ top: 15, right: 10, left: -10, bottom: 25 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} interval={0} angle={-15} textAnchor="end" />
                        <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                        <Tooltip
                          formatter={(val) => [`${val.toLocaleString()} items`, 'Products in Catalog']}
                          contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        />
                        <Bar dataKey="products" fill="#0d9488" radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* 2. Interaction Breakdown */}
                <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
                      <TrendingUp className="w-4 h-4 text-brand-600" />
                      <span>Interaction Types Recorded</span>
                    </div>
                    <span className="text-[11px] text-slate-400 font-medium">
                      {analytics?.overview?.total_interactions || 0} Total Events
                    </span>
                  </div>

                  <div className="h-64 w-full flex items-center justify-center">
                    {interactionData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={interactionData}
                            cx="50%"
                            cy="50%"
                            innerRadius={55}
                            outerRadius={85}
                            paddingAngle={5}
                            dataKey="value"
                          >
                            {interactionData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip
                            formatter={(val, name) => [`${val} records`, name]}
                            contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0' }}
                          />
                          <Legend verticalAlign="bottom" height={36} iconType="circle" />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-xs text-slate-400">No interaction events recorded in SQLite yet.</p>
                    )}
                  </div>
                </div>

                {/* 3. Daily Interaction Activity Trend */}
                <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
                      <Calendar className="w-4 h-4 text-indigo-600" />
                      <span>Interaction Timeline (Database Timestamps)</span>
                    </div>
                    <span className="text-[11px] text-slate-400 font-medium">Daily Aggregation</span>
                  </div>

                  <div className="h-64 w-full">
                    {timelineData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={timelineData} margin={{ top: 15, right: 10, left: -20, bottom: 25 }}>
                          <defs>
                            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                          <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} interval={Math.ceil(timelineData.length / 7)} angle={-15} textAnchor="end" />
                          <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                          <Tooltip
                            formatter={(val) => [`${val} events`, 'Interactions']}
                            contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0' }}
                          />
                          <Area type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-xs text-slate-400">
                        No timestamped activity recorded.
                      </div>
                    )}
                  </div>
                </div>

                {/* 4. Recommendation Algorithm Usage */}
                <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
                      <Sparkles className="w-4 h-4 text-brand-600" />
                      <span>Recommendation Engine Algorithm Logs</span>
                    </div>
                    <span className="text-[11px] text-slate-400 font-medium">
                      {analytics?.overview?.total_recommendation_calls || 0} Total Logged
                    </span>
                  </div>

                  <div className="h-64 w-full flex items-center justify-center">
                    {algorithmData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={algorithmData}
                            cx="50%"
                            cy="50%"
                            innerRadius={55}
                            outerRadius={85}
                            paddingAngle={5}
                            dataKey="value"
                          >
                            {algorithmData.map((entry, index) => (
                              <Cell key={`algo-cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip
                            formatter={(val, name) => [`${val} recommendations`, name]}
                            contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0' }}
                          />
                          <Legend verticalAlign="bottom" height={36} iconType="circle" />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <p className="text-xs text-slate-400">No recommendation logs registered yet.</p>
                    )}
                  </div>
                </div>
              </div>

              {/* System & Dataset Health Status Card */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm">
                <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm pb-4 border-b border-slate-100">
                  <Server className="w-4 h-4 text-emerald-600" />
                  <span>Production System & Recommendation Model Health</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 pt-4">
                  <div className="flex items-start space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-bold text-slate-800">SQLite Database</h4>
                      <p className="text-[11px] text-slate-500">Connected & Verified</p>
                      <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                        File Size: {(Number(analytics?.system_status?.database_size_bytes || 0) / (1024 * 1024)).toFixed(2)} MB
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-bold text-slate-800">Trained ML Models</h4>
                      <p className="text-[11px] text-slate-500">SVD (k=30) + TF-IDF Active</p>
                      <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                        4 Services In-Memory
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-bold text-slate-800">Dataset Verification</h4>
                      <p className="text-[11px] text-slate-500">Amazon Reviews 2023</p>
                      <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                        8,337 Products Processed
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-bold text-slate-800">Offline Evaluation</h4>
                      <p className="text-[11px] text-slate-500">Phase 3 Reports Loaded</p>
                      <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                        N=2,064 Test Users
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: MODEL EVALUATION (PHASE 3) */}
          {activeTab === 'models' && (
            <div className="space-y-8 animate-fade-in">
              {/* Model Comparison Chart */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div>
                    <h3 className="text-base font-extrabold text-slate-900 flex items-center space-x-2">
                      <Cpu className="w-5 h-5 text-indigo-600" />
                      <span>Offline Model Comparison at K=10 (Test Users N=2,064)</span>
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Actual empirical metrics measured during Phase 3 offline temporal evaluation.
                    </p>
                  </div>
                  <span className="text-xs font-semibold px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-full border border-indigo-200">
                    Source: reports/model_comparison.csv
                  </span>
                </div>

                <div className="h-72 w-full pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={modelComparisonChartData} margin={{ top: 15, right: 20, left: 0, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="model" tick={{ fontSize: 11, fill: '#475569' }} />
                      <YAxis tick={{ fontSize: 11, fill: '#475569' }} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0' }}
                      />
                      <Legend verticalAlign="top" height={36} iconType="circle" />
                      <Bar dataKey="recallPct" name="Recall@10 (%)" fill="#6366f1" radius={[6, 6, 0, 0]} />
                      <Bar dataKey="precisionPct" name="Precision@10 (%)" fill="#0d9488" radius={[6, 6, 0, 0]} />
                      <Bar dataKey="ndcg" name="NDCG@10" fill="#f59e0b" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Best Performers Banner (Real Measured Metrics Only) */}
              {modelMetrics?.best_metrics_k10 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-emerald-50/70 border border-emerald-200 p-4 rounded-2xl">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 block">
                      Best Recall@10
                    </span>
                    <p className="text-lg font-black text-emerald-950 mt-1">
                      {modelMetrics.best_metrics_k10['Recall@K']?.model}
                    </p>
                    <p className="text-xs font-mono font-semibold text-emerald-700 mt-0.5">
                      {(Number(modelMetrics.best_metrics_k10['Recall@K']?.value || 0) * 100).toFixed(2)}%
                    </p>
                  </div>

                  <div className="bg-teal-50/70 border border-teal-200 p-4 rounded-2xl">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-teal-800 block">
                      Best Precision@10
                    </span>
                    <p className="text-lg font-black text-teal-950 mt-1">
                      {modelMetrics.best_metrics_k10['Precision@K']?.model}
                    </p>
                    <p className="text-xs font-mono font-semibold text-teal-700 mt-0.5">
                      {(Number(modelMetrics.best_metrics_k10['Precision@K']?.value || 0) * 100).toFixed(2)}%
                    </p>
                  </div>

                  <div className="bg-indigo-50/70 border border-indigo-200 p-4 rounded-2xl">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-800 block">
                      Best Ranking (NDCG@10)
                    </span>
                    <p className="text-lg font-black text-indigo-950 mt-1">
                      {modelMetrics.best_metrics_k10['NDCG@K']?.model}
                    </p>
                    <p className="text-xs font-mono font-semibold text-indigo-700 mt-0.5">
                      {modelMetrics.best_metrics_k10['NDCG@K']?.value}
                    </p>
                  </div>

                  <div className="bg-amber-50/70 border border-amber-200 p-4 rounded-2xl">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-amber-800 block">
                      Best Catalog Diversity
                    </span>
                    <p className="text-lg font-black text-amber-950 mt-1">
                      {modelMetrics.best_metrics_k10['Diversity@K']?.model}
                    </p>
                    <p className="text-xs font-mono font-semibold text-amber-700 mt-0.5">
                      {modelMetrics.best_metrics_k10['Diversity@K']?.value}
                    </p>
                  </div>
                </div>
              )}

              {/* Complete Offline Evaluation Table */}
              {modelMetrics?.model_comparison && (
                <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <h3 className="text-base font-extrabold text-slate-900">
                      Phase 3 Offline Benchmark Results Matrix
                    </h3>
                    <span className="text-xs text-slate-400">Fixed Random Seed 42</span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-400 uppercase tracking-wider font-semibold">
                          <th className="py-3 px-3">Model</th>
                          <th className="py-3 px-3 text-center">K</th>
                          <th className="py-3 px-3 text-right">Precision@K</th>
                          <th className="py-3 px-3 text-right">Recall@K</th>
                          <th className="py-3 px-3 text-right">F1@K</th>
                          <th className="py-3 px-3 text-right">NDCG@K</th>
                          <th className="py-3 px-3 text-right">MAP@K</th>
                          <th className="py-3 px-3 text-right">Coverage (%)</th>
                          <th className="py-3 px-3 text-right">Diversity</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-medium">
                        {modelMetrics.model_comparison.map((m, idx) => {
                          const isHybrid = m.Model?.includes('Hybrid');
                          return (
                            <tr
                              key={idx}
                              className={`hover:bg-slate-50 transition-colors ${
                                isHybrid ? 'bg-indigo-50/40 text-indigo-950 font-bold' : 'text-slate-800'
                              }`}
                            >
                              <td className="py-3.5 px-3 flex items-center space-x-1.5">
                                <span>{m.Model}</span>
                                {isHybrid && (
                                  <span className="text-[10px] bg-brand-600 text-white px-1.5 py-0.2 rounded font-bold">
                                    HYBRID
                                  </span>
                                )}
                              </td>
                              <td className="py-3.5 px-3 text-center text-slate-400">{m.K}</td>
                              <td className="py-3.5 px-3 text-right font-mono">
                                {typeof m['Precision@K'] === 'number' ? `${(m['Precision@K'] * 100).toFixed(2)}%` : m['Precision@K']}
                              </td>
                              <td className="py-3.5 px-3 text-right font-mono">
                                {typeof m['Recall@K'] === 'number' ? `${(m['Recall@K'] * 100).toFixed(2)}%` : m['Recall@K']}
                              </td>
                              <td className="py-3.5 px-3 text-right font-mono">
                                {typeof m['F1@K'] === 'number' ? `${(m['F1@K'] * 100).toFixed(2)}%` : m['F1@K']}
                              </td>
                              <td className="py-3.5 px-3 text-right font-mono">{m['NDCG@K']}</td>
                              <td className="py-3.5 px-3 text-right font-mono">{m['MAP@K']}</td>
                              <td className="py-3.5 px-3 text-right font-mono">{m['Coverage@K (%)']}%</td>
                              <td className="py-3.5 px-3 text-right font-mono">{m['Diversity@K']}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Hybrid Alpha Sensitivity Experiments Table */}
              {modelMetrics?.alpha_experiments && modelMetrics.alpha_experiments.length > 0 && (
                <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                    <div>
                      <h3 className="text-base font-extrabold text-slate-900">
                        Hybrid α Weight Sensitivity Analysis (K=10)
                      </h3>
                      <p className="text-xs text-slate-500">
                        Empirical validation across alpha values [0.00, 0.25, 0.50, 0.75, 1.00].
                      </p>
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200">
                      Optimum Peak: α = 0.25
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-400 uppercase tracking-wider font-semibold">
                          <th className="py-3 px-3">Alpha Setting</th>
                          <th className="py-3 px-3 text-center">Weight Split (CF / CB)</th>
                          <th className="py-3 px-3 text-right">Recall@10</th>
                          <th className="py-3 px-3 text-right">Precision@10</th>
                          <th className="py-3 px-3 text-right">NDCG@10</th>
                          <th className="py-3 px-3 text-right">Coverage (%)</th>
                          <th className="py-3 px-3 text-right">Diversity</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-medium">
                        {modelMetrics.alpha_experiments.map((exp, idx) => {
                          const isOptimum = Number(exp.Alpha) === 0.25;
                          return (
                            <tr
                              key={idx}
                              className={`hover:bg-slate-50 transition-colors ${
                                isOptimum ? 'bg-emerald-50/80 font-bold text-emerald-950' : 'text-slate-800'
                              }`}
                            >
                              <td className="py-3.5 px-3 flex items-center space-x-2">
                                <span>{exp.Model}</span>
                                {isOptimum && (
                                  <span className="text-[10px] bg-emerald-600 text-white px-2 py-0.5 rounded font-bold">
                                    OPTIMUM
                                  </span>
                                )}
                              </td>
                              <td className="py-3.5 px-3 text-center font-mono text-slate-500">
                                {Math.round(exp.Alpha * 100)}% / {Math.round((1 - exp.Alpha) * 100)}%
                              </td>
                              <td className="py-3.5 px-3 text-right font-mono">
                                {(Number(exp['Recall@K'] || 0) * 100).toFixed(2)}%
                              </td>
                              <td className="py-3.5 px-3 text-right font-mono">
                                {(Number(exp['Precision@K'] || 0) * 100).toFixed(2)}%
                              </td>
                              <td className="py-3.5 px-3 text-right font-mono">{exp['NDCG@K']}</td>
                              <td className="py-3.5 px-3 text-right font-mono">{exp['Coverage@K (%)']}%</td>
                              <td className="py-3.5 px-3 text-right font-mono">{exp['Diversity@K']}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: REAL DATA TABLES */}
          {activeTab === 'tables' && (
            <div className="space-y-8 animate-fade-in">
              {/* Top Products Table */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                  <div>
                    <h3 className="text-base font-extrabold text-slate-900 flex items-center space-x-2">
                      <Award className="w-5 h-5 text-amber-500" />
                      <span>Top Interacted Catalog Products</span>
                    </h3>
                    <p className="text-xs text-slate-500">
                      Ranked dynamically by total user interaction events in SQLite database.
                    </p>
                  </div>
                  <span className="text-xs text-slate-400 font-medium">Top 10 Items</span>
                </div>

                {analytics?.products?.top_interacted?.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-400 uppercase tracking-wider font-semibold">
                          <th className="py-3 px-3 text-center">Rank</th>
                          <th className="py-3 px-3">Product Title</th>
                          <th className="py-3 px-3">Category</th>
                          <th className="py-3 px-3 text-right">Price</th>
                          <th className="py-3 px-3 text-center">Rating</th>
                          <th className="py-3 px-3 text-right">Interactions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-medium">
                        {analytics.products.top_interacted.map((p, idx) => (
                          <tr key={p.id} className="hover:bg-slate-50 transition-colors">
                            <td className="py-3 px-3 text-center font-bold text-slate-400">#{idx + 1}</td>
                            <td className="py-3 px-3 font-semibold text-slate-900 max-w-xs truncate" title={p.title}>
                              {p.title}
                            </td>
                            <td className="py-3 px-3 text-slate-600">{p.category}</td>
                            <td className="py-3 px-3 text-right font-mono font-semibold text-slate-800">
                              ${p.price.toFixed(2)}
                            </td>
                            <td className="py-3 px-3 text-center">
                              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 font-bold text-[11px]">
                                <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                                <span>{p.rating}</span>
                              </span>
                            </td>
                            <td className="py-3 px-3 text-right font-black text-brand-700">
                              {p.interaction_count}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 py-6 text-center">No interacted products found.</p>
                )}
              </div>

              {/* Category Breakdown Table */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-base font-extrabold text-slate-900">
                    Category Metrics & Performance
                  </h3>
                  <span className="text-xs text-slate-400 font-medium">3 Catalog Categories</span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-400 uppercase tracking-wider font-semibold">
                        <th className="py-3 px-3">Category Name</th>
                        <th className="py-3 px-3 text-right">Products Count</th>
                        <th className="py-3 px-3 text-right">Recorded Interactions</th>
                        <th className="py-3 px-3 text-right">Catalog Avg Rating</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 font-medium">
                      {analytics?.categories_detailed?.map((cat, idx) => (
                        <tr key={idx} className="hover:bg-slate-50 transition-colors">
                          <td className="py-3 px-3 font-bold text-slate-900">{cat.category}</td>
                          <td className="py-3 px-3 text-right font-mono font-semibold text-slate-800">
                            {cat.product_count.toLocaleString()}
                          </td>
                          <td className="py-3 px-3 text-right font-mono font-bold text-brand-700">
                            {cat.interaction_count}
                          </td>
                          <td className="py-3 px-3 text-right font-mono text-amber-700">
                            ★ {cat.avg_rating}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Recent Interactions Table */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-base font-extrabold text-slate-900 flex items-center space-x-2">
                    <Activity className="w-5 h-5 text-teal-600" />
                    <span>Recent User Interaction Events</span>
                  </h3>
                  <span className="text-xs text-slate-400 font-medium">Latest 15 Events in SQLite</span>
                </div>

                {analytics?.recent_interactions?.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-400 uppercase tracking-wider font-semibold">
                          <th className="py-3 px-3">ID</th>
                          <th className="py-3 px-3">User</th>
                          <th className="py-3 px-3">Product</th>
                          <th className="py-3 px-3 text-center">Type</th>
                          <th className="py-3 px-3 text-center">Rating</th>
                          <th className="py-3 px-3 text-right">Timestamp</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-medium">
                        {analytics.recent_interactions.map((i) => (
                          <tr key={i.id} className="hover:bg-slate-50 transition-colors">
                            <td className="py-3 px-3 text-slate-400 font-mono">#{i.id}</td>
                            <td className="py-3 px-3 font-semibold text-slate-800">{i.user_email}</td>
                            <td className="py-3 px-3 text-slate-700 max-w-xs truncate" title={i.product_title}>
                              {i.product_title}
                            </td>
                            <td className="py-3 px-3 text-center">
                              <span
                                className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider text-white"
                                style={{
                                  backgroundColor: interactionColors[i.interaction_type.toLowerCase()] || '#64748b',
                                }}
                              >
                                {i.interaction_type}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-center font-mono">
                              {i.rating !== null ? `★ ${i.rating}` : '—'}
                            </td>
                            <td className="py-3 px-3 text-right font-mono text-slate-500 text-[11px]">
                              {i.timestamp || '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 py-6 text-center">No interaction events recorded yet.</p>
                )}
              </div>

              {/* Recent Recommendation Logs Table */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-base font-extrabold text-slate-900 flex items-center space-x-2">
                    <Sparkles className="w-5 h-5 text-brand-600" />
                    <span>Recent Recommendation Logs</span>
                  </h3>
                  <span className="text-xs text-slate-400 font-medium">Latest 15 Recommendations</span>
                </div>

                {analytics?.recent_recommendation_logs?.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate-200 text-slate-400 uppercase tracking-wider font-semibold">
                          <th className="py-3 px-3">Log ID</th>
                          <th className="py-3 px-3">User</th>
                          <th className="py-3 px-3">Recommended Product</th>
                          <th className="py-3 px-3 text-center">Algorithm</th>
                          <th className="py-3 px-3 text-right">Predicted Score</th>
                          <th className="py-3 px-3 text-right">Logged At</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-medium">
                        {analytics.recent_recommendation_logs.map((log) => (
                          <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                            <td className="py-3 px-3 text-slate-400 font-mono">#{log.id}</td>
                            <td className="py-3 px-3 font-semibold text-slate-800">{log.user_email}</td>
                            <td className="py-3 px-3 text-slate-700 max-w-xs truncate" title={log.product_title}>
                              {log.product_title}
                            </td>
                            <td className="py-3 px-3 text-center">
                              <span
                                className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider text-white"
                                style={{
                                  backgroundColor: algoColors[log.algorithm.toLowerCase()] || '#64748b',
                                }}
                              >
                                {log.algorithm.replace('_', ' ')}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-right font-mono font-bold text-brand-700">
                              {log.score}
                            </td>
                            <td className="py-3 px-3 text-right font-mono text-slate-500 text-[11px]">
                              {log.created_at || '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 py-6 text-center">No recommendation logs recorded yet.</p>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AdminDashboard;
