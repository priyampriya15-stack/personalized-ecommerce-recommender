import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Star, Heart, ShoppingBag, Sparkles, ImageOff } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import cartService from '../services/cartService';
import interactionService from '../services/interactionService';

export const ProductCard = ({ product, onToast }) => {
  const { isAuthenticated, updateCartCount, cartCount } = useAuth();
  const [imgError, setImgError] = useState(false);
  const [liked, setLiked] = useState(false);
  const [addingToCart, setAddingToCart] = useState(false);

  const productId = product.id || product.product_id;
  const title = product.title || product.product_title || 'Untitled Product';
  const category = product.category || 'General';
  const price = typeof product.price === 'number' ? product.price : parseFloat(product.price) || 0.0;
  const rating = typeof product.rating === 'number' ? product.rating : parseFloat(product.rating) || 4.5;
  const score = product.score !== undefined ? product.score : product.similarity_score;
  const explanation = product.explanation;
  const algorithm = product.algorithm;

  const handleLike = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      if (onToast) onToast('Please log in to save favorites.', 'info');
      return;
    }

    try {
      setLiked(!liked);
      await interactionService.recordInteraction({
        productId,
        interactionType: 'like',
      });
      if (onToast) onToast(liked ? 'Removed from liked items.' : 'Added to favorites!', 'success');
    } catch {
      setLiked(liked);
      if (onToast) onToast('Failed to record like.', 'error');
    }
  };

  const handleAddToCart = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      if (onToast) onToast('Please log in to add items to your cart.', 'info');
      return;
    }

    try {
      setAddingToCart(true);
      const res = await cartService.addToCart(productId, 1);
      if (res && res.data) {
        updateCartCount(res.data.total_items ?? (cartCount + 1));
      } else {
        updateCartCount(cartCount + 1);
      }
      if (onToast) onToast(`"${title.slice(0, 30)}..." added to cart!`, 'success');
    } catch (err) {
      if (onToast) onToast(err.message || 'Failed to add item to cart.', 'error');
    } finally {
      setAddingToCart(false);
    }
  };

  return (
    <div className="group relative bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-xl hover:border-brand-200 transition-all duration-300 flex flex-col h-full overflow-hidden hover:-translate-y-1">
      {/* Algorithm Badge if present */}
      {algorithm && (
        <div className="absolute top-3 left-3 z-10">
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-brand-500/95 text-white backdrop-blur-md shadow-sm">
            <Sparkles className="w-3 h-3" />
            <span className="capitalize">{algorithm.replace('_', ' ')}</span>
            {score !== undefined && (
              <span className="opacity-90 ml-1 font-mono">
                {score < 1 ? `${Math.round(score * 100)}%` : score.toFixed(1)}
              </span>
            )}
          </span>
        </div>
      )}

      {/* Like / Wishlist Button */}
      <button
        onClick={handleLike}
        title={liked ? 'Unlike' : 'Like'}
        className={`absolute top-3 right-3 z-10 p-2 rounded-full backdrop-blur-md transition-all ${
          liked
            ? 'bg-rose-50 text-rose-500 border border-rose-200'
            : 'bg-white/80 text-slate-400 hover:text-rose-500 hover:bg-white border border-slate-200/60'
        }`}
      >
        <Heart className={`w-4 h-4 ${liked ? 'fill-rose-500' : ''}`} />
      </button>

      {/* Product Image */}
      <Link to={`/products/${productId}`} className="relative aspect-square w-full overflow-hidden bg-slate-50 flex items-center justify-center p-4">
        {product.image_url && !imgError ? (
          <img
            src={product.image_url}
            alt={title}
            onError={() => setImgError(true)}
            className="w-full h-full object-contain mix-blend-multiply group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-slate-300">
            <ImageOff className="w-12 h-12 mb-1" />
            <span className="text-xs font-medium text-slate-400">NexStore Product</span>
          </div>
        )}
      </Link>

      {/* Card Content */}
      <div className="p-4 flex flex-col flex-1">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs font-medium text-brand-600 bg-brand-50 px-2 py-0.5 rounded-md">
            {category}
          </span>
          <div className="flex items-center text-amber-500 space-x-1 text-xs font-semibold">
            <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
            <span>{rating.toFixed(1)}</span>
          </div>
        </div>

        <Link
          to={`/products/${productId}`}
          className="text-sm font-semibold text-slate-900 group-hover:text-brand-600 transition-colors line-clamp-2 mb-2 leading-snug"
          title={title}
        >
          {title}
        </Link>

        {/* Dynamic Explanation from ML model */}
        {explanation && (
          <p className="text-xs text-slate-500 italic bg-slate-50 p-1.5 rounded-lg border border-slate-100 mb-3 line-clamp-2">
            💡 {explanation}
          </p>
        )}

        {/* Price & Action */}
        <div className="mt-auto pt-3 border-t border-slate-100 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 block">Price</span>
            <span className="text-lg font-bold text-slate-900">
              ${price.toFixed(2)}
            </span>
          </div>

          <button
            onClick={handleAddToCart}
            disabled={addingToCart}
            className="inline-flex items-center space-x-1.5 px-3 py-2 bg-brand-600 hover:bg-brand-700 active:scale-95 text-white rounded-xl text-xs font-semibold shadow-sm shadow-brand-500/20 transition-all disabled:opacity-50"
          >
            <ShoppingBag className="w-3.5 h-3.5" />
            <span>Add</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
