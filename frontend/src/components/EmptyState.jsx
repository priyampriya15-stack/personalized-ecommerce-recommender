import React from 'react';
import { PackageOpen, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const EmptyState = ({
  icon: Icon = PackageOpen,
  title = 'No items found',
  description = 'There are no items to display at this moment.',
  actionText = 'Browse Catalog',
  actionLink = '/products',
  onAction,
}) => (
  <div className="flex flex-col items-center justify-center py-16 px-4 text-center max-w-md mx-auto">
    <div className="w-16 h-16 rounded-2xl bg-teal-50 border border-teal-100 flex items-center justify-center text-teal-600 mb-4 shadow-sm">
      <Icon className="w-8 h-8" />
    </div>
    <h3 className="text-xl font-bold text-slate-800 mb-2">{title}</h3>
    <p className="text-slate-500 text-sm mb-6 leading-relaxed">{description}</p>
    {onAction ? (
      <button
        onClick={onAction}
        className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-sm font-semibold transition-all shadow-md shadow-brand-500/20"
      >
        <span>{actionText}</span>
        <ArrowRight className="w-4 h-4" />
      </button>
    ) : actionLink ? (
      <Link
        to={actionLink}
        className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-sm font-semibold transition-all shadow-md shadow-brand-500/20"
      >
        <span>{actionText}</span>
        <ArrowRight className="w-4 h-4" />
      </Link>
    ) : null}
  </div>
);

export default EmptyState;
