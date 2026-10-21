import React from 'react';

export const ProductCardSkeleton = () => (
  <div className="bg-white rounded-2xl border border-slate-100 p-4 shadow-sm animate-pulse flex flex-col h-full">
    <div className="w-full aspect-square bg-slate-200 rounded-xl mb-4" />
    <div className="h-4 bg-slate-200 rounded w-1/3 mb-2" />
    <div className="h-5 bg-slate-200 rounded w-full mb-2" />
    <div className="h-4 bg-slate-200 rounded w-3/4 mb-4" />
    <div className="mt-auto flex items-center justify-between pt-2">
      <div className="h-6 bg-slate-200 rounded w-1/4" />
      <div className="h-9 bg-slate-200 rounded-xl w-24" />
    </div>
  </div>
);

export const ProductGridSkeleton = ({ count = 8 }) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
    {Array.from({ length: count }).map((_, i) => (
      <ProductCardSkeleton key={i} />
    ))}
  </div>
);

export const TableSkeleton = ({ rows = 5 }) => (
  <div className="space-y-3 animate-pulse">
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="h-12 bg-slate-100 rounded-lg w-full" />
    ))}
  </div>
);

export default ProductGridSkeleton;
