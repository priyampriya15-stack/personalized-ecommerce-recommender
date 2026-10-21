import React from 'react';
import ProductCard from './ProductCard';
import { ProductGridSkeleton } from './LoadingSkeleton';
import EmptyState from './EmptyState';

export const ProductGrid = ({
  products = [],
  loading = false,
  emptyTitle = 'No products found',
  emptyMessage = 'Try adjusting your search query or filter options.',
  onToast,
  skeletonCount = 8,
}) => {
  if (loading) {
    return <ProductGridSkeleton count={skeletonCount} />;
  }

  if (!products || products.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyMessage} />;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
      {products.map((product) => (
        <ProductCard
          key={product.id || product.product_id}
          product={product}
          onToast={onToast}
        />
      ))}
    </div>
  );
};

export default ProductGrid;
