import React from 'react';
import { Sparkles, Brain, Cpu, Flame } from 'lucide-react';
import ProductCard from './ProductCard';
import { ProductCardSkeleton } from './LoadingSkeleton';

export const RecommendationSection = ({
  title,
  subtitle,
  algorithm = 'hybrid',
  recommendations = [],
  loading = false,
  onToast,
  maxItems = 4,
}) => {
  const iconConfig = {
    hybrid: {
      icon: Sparkles,
      color: 'bg-teal-50 text-teal-600 border-teal-200',
      badge: 'Hybrid (CF + CB)',
    },
    collaborative: {
      icon: Brain,
      color: 'bg-indigo-50 text-indigo-600 border-indigo-200',
      badge: 'Collaborative SVD',
    },
    content_based: {
      icon: Cpu,
      color: 'bg-amber-50 text-amber-600 border-amber-200',
      badge: 'TF-IDF Content',
    },
    popularity: {
      icon: Flame,
      color: 'bg-rose-50 text-rose-600 border-rose-200',
      badge: 'Bayesian Popularity',
    },
  }[algorithm] || {
    icon: Sparkles,
    color: 'bg-teal-50 text-teal-600 border-teal-200',
    badge: 'Recommendation',
  };

  const IconComponent = iconConfig.icon;
  const displayItems = recommendations.slice(0, maxItems);

  if (!loading && displayItems.length === 0) {
    return null;
  }

  return (
    <section className="mb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 pb-3 border-b border-slate-200/60">
        <div className="flex items-center space-x-3 mb-2 sm:mb-0">
          <div className={`p-2.5 rounded-xl border ${iconConfig.color}`}>
            <IconComponent className="w-5 h-5" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h2>
              <span className={`text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${iconConfig.color}`}>
                {iconConfig.badge}
              </span>
            </div>
            {subtitle && <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
        {loading
          ? Array.from({ length: maxItems }).map((_, i) => <ProductCardSkeleton key={i} />)
          : displayItems.map((prod) => (
              <ProductCard
                key={prod.id || prod.product_id}
                product={prod}
                onToast={onToast}
              />
            ))}
      </div>
    </section>
  );
};

export default RecommendationSection;
