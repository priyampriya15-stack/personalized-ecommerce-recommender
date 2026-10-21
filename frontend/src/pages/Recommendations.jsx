import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, Brain, Cpu, Flame, Sliders, Info, LogIn } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import recommendationService from '../services/recommendationService';
import RecommendationSection from '../components/RecommendationSection';
import Toast from '../components/Toast';

export const Recommendations = () => {
  const { user, isAuthenticated } = useAuth();

  const [activeTab, setActiveTab] = useState('hybrid');
  const [hybridRecs, setHybridRecs] = useState([]);
  const [cfRecs, setCfRecs] = useState([]);
  const [cbRecs, setCbRecs] = useState([]);
  const [popularRecs, setPopularRecs] = useState([]);

  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const showToast = (message, type = 'success') => setToast({ message, type });

  useEffect(() => {
    let isMounted = true;

    const fetchAllRecs = async () => {
      try {
        setLoading(true);

        // Fetch popular for all users
        const popRes = await recommendationService.getPopularRecommendations({ limit: 8 });
        if (isMounted && popRes && popRes.data) {
          setPopularRecs(popRes.data);
        }

        // Fetch personalized algorithms if authenticated
        if (isAuthenticated && user?.id) {
          const [hybRes, cfRes, cbRes] = await Promise.allSettled([
            recommendationService.getHybridRecommendations(user.id, { limit: 8 }),
            recommendationService.getCollaborativeRecommendations(user.id, { limit: 8 }),
            recommendationService.getContentBasedRecommendations(user.id, { limit: 8 }),
          ]);

          if (isMounted) {
            if (hybRes.status === 'fulfilled' && hybRes.value?.data) {
              setHybridRecs(hybRes.value.data);
            }
            if (cfRes.status === 'fulfilled' && cfRes.value?.data) {
              setCfRecs(cfRes.value.data);
            }
            if (cbRes.status === 'fulfilled' && cbRes.value?.data) {
              setCbRecs(cbRes.value.data);
            }
          }
        }
      } catch (err) {
        console.error('Error fetching recommendations:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchAllRecs();

    return () => {
      isMounted = false;
    };
  }, [isAuthenticated, user?.id]);

  const tabs = [
    { id: 'hybrid', label: 'Hybrid AI (CF + CB)', icon: Sparkles, count: hybridRecs.length },
    { id: 'collaborative', label: 'Collaborative SVD', icon: Brain, count: cfRecs.length },
    { id: 'content', label: 'TF-IDF Content', icon: Cpu, count: cbRecs.length },
    { id: 'popular', label: 'Bayesian Popularity', icon: Flame, count: popularRecs.length },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      {/* Header */}
      <div className="pb-6 border-b border-slate-200">
        <div className="flex items-center space-x-2 text-brand-600 mb-1">
          <Sparkles className="w-5 h-5 text-brand-500" />
          <span className="text-xs font-bold uppercase tracking-wider">Machine Learning Engine</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Personalized Recommendation Hub
        </h1>
        <p className="text-sm text-slate-500 mt-1 max-w-2xl">
          Compare our multi-modal recommendation models side-by-side. All recommendations are generated on-the-fly using trained Truncated SVD, TF-IDF cosine similarity, and Bayesian statistics.
        </p>
      </div>

      {/* Guest Login Callout Banner */}
      {!isAuthenticated && (
        <div className="rounded-2xl bg-gradient-to-r from-teal-50 to-emerald-50 border border-teal-200 p-6 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-white rounded-xl text-teal-600 shadow-sm border border-teal-100">
              <Info className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Viewing Non-Personalized Catalog Baseline
              </h3>
              <p className="text-xs text-slate-600 mt-0.5">
                Log in or create a free account to unlock personalized Collaborative Filtering and Content-Based models tailored to your taste.
              </p>
            </div>
          </div>

          <Link
            to="/login"
            className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-bold shadow-sm whitespace-nowrap"
          >
            <LogIn className="w-4 h-4" />
            <span>Log In for Personalization</span>
          </Link>
        </div>
      )}

      {/* Algorithm Tabs */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-2 border-b border-slate-200 no-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all duration-200 ${
                isActive
                  ? 'bg-slate-900 text-white shadow-md scale-105'
                  : 'bg-white hover:bg-slate-100 text-slate-600 border border-slate-200'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-brand-400' : 'text-slate-500'}`} />
              <span>{tab.label}</span>
              {tab.count > 0 && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    isActive ? 'bg-slate-700 text-white' : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {activeTab === 'hybrid' && (
          <RecommendationSection
            title="Hybrid Recommendation (α · CF + (1 - α) · CB)"
            subtitle="Normalized combination of latent user interaction factors and product text content similarity"
            algorithm="hybrid"
            recommendations={hybridRecs.length > 0 ? hybridRecs : popularRecs}
            loading={loading}
            onToast={showToast}
            maxItems={8}
          />
        )}

        {activeTab === 'collaborative' && (
          <RecommendationSection
            title="Collaborative Filtering (Truncated SVD)"
            subtitle="Learns latent user and item factor matrices (k=30) from 39,000+ interaction histories"
            algorithm="collaborative"
            recommendations={cfRecs.length > 0 ? cfRecs : popularRecs}
            loading={loading}
            onToast={showToast}
            maxItems={8}
          />
        )}

        {activeTab === 'content' && (
          <RecommendationSection
            title="Content-Based Filtering (TF-IDF & Cosine Similarity)"
            subtitle="Matches your preference vector against product titles, categories, and descriptions"
            algorithm="content_based"
            recommendations={cbRecs.length > 0 ? cbRecs : popularRecs}
            loading={loading}
            onToast={showToast}
            maxItems={8}
          />
        )}

        {activeTab === 'popular' && (
          <RecommendationSection
            title="Bayesian Weighted Popularity Baseline"
            subtitle="Calculates Bayesian smoothed review scores (m=5, C=4.22) across entire verified catalog"
            algorithm="popularity"
            recommendations={popularRecs}
            loading={loading}
            onToast={showToast}
            maxItems={8}
          />
        )}
      </div>
    </div>
  );
};

export default Recommendations;
