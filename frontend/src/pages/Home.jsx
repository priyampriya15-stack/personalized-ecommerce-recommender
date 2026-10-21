import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, ShieldCheck, Zap, HeartHandshake } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import recommendationService from '../services/recommendationService';
import productService from '../services/productService';
import RecommendationSection from '../components/RecommendationSection';
import CategoryFilter from '../components/CategoryFilter';
import Toast from '../components/Toast';

export const Home = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [popularRecs, setPopularRecs] = useState([]);
  const [hybridRecs, setHybridRecs] = useState([]);
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [loadingPopular, setLoadingPopular] = useState(true);
  const [loadingHybrid, setLoadingHybrid] = useState(false);
  const [loadingFeatured, setLoadingFeatured] = useState(true);
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
  };

  useEffect(() => {
    // Load Popular items for both guests and members
    const fetchPopular = async () => {
      try {
        setLoadingPopular(true);
        const res = await recommendationService.getPopularRecommendations({ limit: 8 });
        if (res && res.data) {
          setPopularRecs(res.data);
        }
      } catch (err) {
        console.error('Failed to load popular recommendations:', err);
      } finally {
        setLoadingPopular(false);
      }
    };

    // Load Featured catalog products
    const fetchFeatured = async () => {
      try {
        setLoadingFeatured(true);
        const res = await productService.getProducts({ limit: 4, sort: 'rating_desc' });
        if (res && res.data && res.data.products) {
          setFeaturedProducts(res.data.products);
        }
      } catch (err) {
        console.error('Failed to load featured products:', err);
      } finally {
        setLoadingFeatured(false);
      }
    };

    fetchPopular();
    fetchFeatured();
  }, []);

  // Fetch Hybrid recommendations for authenticated users
  useEffect(() => {
    if (!isAuthenticated || !user?.id) return;

    const fetchPersonalized = async () => {
      try {
        setLoadingHybrid(true);
        const res = await recommendationService.getHybridRecommendations(user.id, { limit: 4 });
        if (res && res.data) {
          setHybridRecs(res.data);
        }
      } catch (err) {
        console.error('Failed to load hybrid recommendations:', err);
      } finally {
        setLoadingHybrid(false);
      }
    };

    fetchPersonalized();
  }, [isAuthenticated, user?.id]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      {/* Hero Banner */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-teal-950 to-slate-900 text-white p-5 sm:p-8 md:p-14 shadow-2xl border border-teal-900/40">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-500/20 border border-brand-400/30 text-brand-300 text-xs font-semibold mb-6">
            <Sparkles className="w-3.5 h-3.5 text-brand-400" />
            <span>AI-Driven Collaborative & Content-Based Filtering</span>
          </div>

          <h1 className="text-2xl sm:text-4xl md:text-5xl font-extrabold tracking-tight leading-tight mb-4">
            Discover Products <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-300 to-emerald-400">
              Tailored Exactly To You
            </span>
          </h1>

          <p className="text-slate-300 text-sm sm:text-base mb-8 leading-relaxed">
            Experience our hybrid recommendation engine trained on over 39,000 verified interactions. Combining latent SVD factor matrices and TF-IDF semantic embeddings.
          </p>

          <div className="flex flex-wrap items-center gap-4">
            <Link
              to="/products"
              className="inline-flex items-center space-x-2 px-6 py-3.5 bg-brand-500 hover:bg-brand-400 text-slate-950 font-bold rounded-xl text-sm transition-all shadow-lg shadow-brand-500/30 active:scale-95"
            >
              <span>Explore 8,300+ Catalog</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            {!isAuthenticated && (
              <Link
                to="/register"
                className="inline-flex items-center space-x-2 px-6 py-3.5 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-xl text-sm transition-all border border-white/20 backdrop-blur-md"
              >
                <span>Create Personalized Profile</span>
              </Link>
            )}
          </div>
        </div>

        {/* Feature Pills */}
        <div className="mt-12 pt-8 border-t border-white/10 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-slate-300">
          <div className="flex items-center space-x-2">
            <Zap className="w-4 h-4 text-brand-400" />
            <span>Real-time Hybrid Re-ranking</span>
          </div>
          <div className="flex items-center space-x-2">
            <HeartHandshake className="w-4 h-4 text-brand-400" />
            <span>Transparent Explainability</span>
          </div>
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-brand-400" />
            <span>Verified Amazon 2023 Datasets</span>
          </div>
        </div>
      </section>

      {/* Category Pills Navigation */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider">
            Explore By Category
          </h2>
          <Link to="/products" className="text-xs font-semibold text-brand-600 hover:text-brand-700">
            View All Categories →
          </Link>
        </div>
        <CategoryFilter
          onSelectCategory={(cat) => {
            navigate(cat ? `/products?category=${encodeURIComponent(cat)}` : '/products');
          }}
        />
      </section>

      {/* Authenticated: Personalized Hybrid Section */}
      {isAuthenticated && (
        <RecommendationSection
          title="Recommended For You"
          subtitle="Dynamic hybrid blend weighted by your browsing history and category affinities"
          algorithm="hybrid"
          recommendations={hybridRecs}
          loading={loadingHybrid}
          onToast={showToast}
          maxItems={4}
        />
      )}

      {/* Popular Recommendations Section */}
      <RecommendationSection
        title="Trending & Top-Rated Products"
        subtitle="Ranked via Bayesian weighted rating across verified customer reviews"
        algorithm="popularity"
        recommendations={popularRecs}
        loading={loadingPopular}
        onToast={showToast}
        maxItems={4}
      />

      {/* Featured Catalog Items Section */}
      <RecommendationSection
        title="Featured From Our Catalog"
        subtitle="Handpicked high-rated items across Beauty, Appliances, and Digital Music"
        algorithm="content_based"
        recommendations={featuredProducts}
        loading={loadingFeatured}
        onToast={showToast}
        maxItems={4}
      />
    </div>
  );
};

export default Home;
