import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate, useLocation } from 'react-router-dom';
import { Star, Heart, ShoppingBag, ArrowLeft, ImageOff, Check, Cpu, Zap } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import productService from '../services/productService';
import interactionService from '../services/interactionService';
import cartService from '../services/cartService';
import ProductGrid from '../components/ProductGrid';
import ErrorMessage from '../components/ErrorMessage';
import Toast from '../components/Toast';

export const ProductDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, updateCartCount, cartCount } = useAuth();

  const [product, setProduct] = useState(null);
  const [similarProducts, setSimilarProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [error, setError] = useState(null);
  const [imgError, setImgError] = useState(false);

  // Interaction states
  const [quantity, setQuantity] = useState(1);
  const [liked, setLiked] = useState(false);
  const [userRating, setUserRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [addingToCart, setAddingToCart] = useState(false);
  const [toast, setToast] = useState({ message: '', type: 'success' });
  const viewRecordedRef = React.useRef({});

  const showToast = (message, type = 'success') => setToast({ message, type });

  // Fetch product and similar items
  useEffect(() => {
    let isMounted = true;

    const fetchDetails = async () => {
      try {
        setLoading(true);
        setError(null);
        setImgError(false);

        const res = await productService.getProductById(id);
        if (res && res.data && isMounted) {
          setProduct(res.data);

          // Record 'view' event if user is authenticated and not recorded yet on this mount
          if (isAuthenticated && !viewRecordedRef.current[res.data.id]) {
            viewRecordedRef.current[res.data.id] = true;
            interactionService.recordInteraction({
              productId: res.data.id,
              interactionType: 'view',
            }).catch(() => {
              viewRecordedRef.current[res.data.id] = false;
            });
          }

          // Fetch similar products via Content-Based TF-IDF model
          setLoadingSimilar(true);
          productService.getSimilarProducts(res.data.id, 4)
            .then((simRes) => {
              if (isMounted && simRes && simRes.data) {
                setSimilarProducts(simRes.data);
              }
            })
            .catch(() => {})
            .finally(() => {
              if (isMounted) setLoadingSimilar(false);
            });
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Product not found or unavailable.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDetails();

    return () => {
      isMounted = false;
    };
  }, [id, isAuthenticated]);

  const handleLike = async () => {
    if (!isAuthenticated) {
      showToast('Please log in to like this item.', 'info');
      return;
    }
    try {
      setLiked(!liked);
      await interactionService.recordInteraction({
        productId: product.id,
        interactionType: 'like',
      });
      showToast(liked ? 'Removed from liked items.' : 'Added to favorites!', 'success');
    } catch {
      setLiked(liked);
      showToast('Failed to save like interaction.', 'error');
    }
  };

  const handleRate = async (ratingVal) => {
    if (!isAuthenticated) {
      showToast('Please log in to rate this product.', 'info');
      return;
    }
    try {
      setUserRating(ratingVal);
      await interactionService.recordInteraction({
        productId: product.id,
        interactionType: 'rating',
        rating: ratingVal,
      });
      showToast(`Thank you! Rated ${ratingVal} stars.`, 'success');
    } catch {
      showToast('Failed to submit rating.', 'error');
    }
  };

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      showToast('Please log in to add items to your cart.', 'info');
      return;
    }
    try {
      setAddingToCart(true);
      const res = await cartService.addToCart(product.id, quantity);
      if (res && res.data) {
        updateCartCount(res.data.total_items ?? (cartCount + quantity));
      } else {
        updateCartCount(cartCount + quantity);
      }
      showToast(`Added ${quantity} item(s) to cart!`, 'success');
    } catch (err) {
      showToast(err.message || 'Failed to add item to cart.', 'error');
    } finally {
      setAddingToCart(false);
    }
  };

  const handleBuyNow = () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: location } });
      return;
    }
    navigate(`/checkout?productId=${product.id}&quantity=${quantity}`);
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 animate-pulse space-y-8">
        <div className="h-6 bg-slate-200 rounded w-32" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <div className="aspect-square bg-slate-200 rounded-2xl" />
          <div className="space-y-4">
            <div className="h-4 bg-slate-200 rounded w-24" />
            <div className="h-8 bg-slate-200 rounded w-3/4" />
            <div className="h-6 bg-slate-200 rounded w-32" />
            <div className="h-24 bg-slate-200 rounded w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <ErrorMessage
          title="Product Not Found"
          message={error || "The product you requested could not be retrieved from the catalog."}
        />
        <div className="text-center mt-4">
          <Link to="/products" className="text-brand-600 font-semibold hover:underline text-sm">
            ← Return to Product Catalog
          </Link>
        </div>
      </div>
    );
  }

  const price = typeof product.price === 'number' ? product.price : parseFloat(product.price) || 0.0;
  const rating = typeof product.rating === 'number' ? product.rating : parseFloat(product.rating) || 4.5;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />

      {/* Back button */}
      <Link
        to="/products"
        className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-brand-600 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Products</span>
      </Link>

      {/* Product Hero Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-14 bg-white rounded-3xl border border-slate-200/80 p-4 sm:p-8 lg:p-10 shadow-sm">
        {/* Product Media Column */}
        <div className="flex flex-col items-center justify-center bg-slate-50 rounded-2xl p-4 sm:p-6 relative aspect-square">
          {product.image_url && !imgError ? (
            <img
              src={product.image_url}
              alt={product.title}
              onError={() => setImgError(true)}
              className="max-h-[380px] w-auto max-w-full object-contain mix-blend-multiply"
            />
          ) : (
            <div className="flex flex-col items-center justify-center text-slate-300">
              <ImageOff className="w-16 h-16 mb-2" />
              <span className="text-xs font-medium text-slate-400">NexStore Product Image</span>
            </div>
          )}

          <button
            onClick={handleLike}
            className={`absolute top-4 right-4 p-3 rounded-full backdrop-blur-md transition-all shadow-sm ${
              liked
                ? 'bg-rose-50 text-rose-500 border border-rose-200'
                : 'bg-white text-slate-400 hover:text-rose-500 border border-slate-200'
            }`}
          >
            <Heart className={`w-5 h-5 ${liked ? 'fill-rose-500' : ''}`} />
          </button>
        </div>

        {/* Product Meta & Actions Column */}
        <div className="flex flex-col justify-between space-y-6 min-w-0">
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold uppercase tracking-wider text-brand-600 bg-brand-50 px-2.5 py-1 rounded-md border border-brand-200/50">
                {product.category}
              </span>
              <span className="text-xs text-slate-400 font-mono">
                ASIN: {product.external_product_id}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 leading-snug">
              {product.title}
            </h1>

            {/* Rating Stars & Customer Score */}
            <div className="flex items-center space-x-3 pt-1">
              <div className="flex items-center text-amber-500 space-x-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    className={`w-4 h-4 ${
                      star <= Math.round(rating)
                        ? 'fill-amber-400 text-amber-400'
                        : 'text-slate-200'
                    }`}
                  />
                ))}
              </div>
              <span className="text-sm font-bold text-slate-800">{rating.toFixed(1)} / 5.0</span>
              <span className="text-xs text-slate-400">• Verified Customer Reviews</span>
            </div>

            {/* Price Badge */}
            <div className="pt-3">
              <span className="text-3xl font-extrabold text-slate-900">
                ${price.toFixed(2)}
              </span>
              <span className="text-xs text-slate-500 ml-2 font-medium">In Stock & Verified</span>
            </div>

            {/* Description */}
            <div className="pt-4 border-t border-slate-100">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Product Details
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed max-h-48 overflow-y-auto">
                {product.description ||
                  `Experience premium quality in ${product.category}. Thoroughly tested and rated by the Amazon community.`}
              </p>
            </div>
          </div>

          {/* Interactive User Rating */}
          <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-2">
            <span className="text-xs font-bold text-slate-700 block">
              Rate this item to train your recommendation profile:
            </span>
            <div className="flex items-center space-x-1">
              {[1, 2, 3, 4, 5].map((val) => (
                <button
                  key={val}
                  type="button"
                  onMouseEnter={() => setHoverRating(val)}
                  onMouseLeave={() => setHoverRating(0)}
                  onClick={() => handleRate(val)}
                  className="p-1 hover:scale-125 transition-transform"
                >
                  <Star
                    className={`w-5 h-5 ${
                      val <= (hoverRating || userRating)
                        ? 'fill-amber-400 text-amber-400'
                        : 'text-slate-300'
                    }`}
                  />
                </button>
              ))}
              {userRating > 0 && (
                <span className="text-xs font-semibold text-emerald-600 ml-2 flex items-center space-x-1">
                  <Check className="w-3.5 h-3.5" />
                  <span>Recorded ({userRating} Stars)</span>
                </span>
              )}
            </div>
          </div>

          {/* Cart & Buy Now Actions */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2">
            <div className="flex items-center justify-between border border-slate-200 rounded-xl bg-slate-50 p-1 w-full sm:w-auto">
              <button
                type="button"
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-slate-600 hover:bg-white transition-colors"
                aria-label="Decrease quantity"
              >
                -
              </button>
              <span className="w-10 text-center font-bold text-sm text-slate-800">
                {quantity}
              </span>
              <button
                type="button"
                onClick={() => setQuantity(quantity + 1)}
                className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-slate-600 hover:bg-white transition-colors"
                aria-label="Increase quantity"
              >
                +
              </button>
            </div>

            <button
              id="add-to-cart-button"
              type="button"
              onClick={handleAddToCart}
              disabled={addingToCart}
              className="flex-1 inline-flex items-center justify-center space-x-2 py-3.5 px-5 bg-slate-900 hover:bg-slate-800 active:scale-95 text-white font-bold rounded-xl text-sm shadow-md transition-all disabled:opacity-50"
            >
              <ShoppingBag className="w-4 h-4" />
              <span>{addingToCart ? 'Adding...' : 'Add to Cart'}</span>
            </button>

            <button
              id="buy-now-button"
              type="button"
              onClick={handleBuyNow}
              className="flex-1 inline-flex items-center justify-center space-x-2 py-3.5 px-5 bg-brand-600 hover:bg-brand-700 active:scale-95 text-white font-bold rounded-xl text-sm shadow-lg shadow-brand-500/25 transition-all"
            >
              <Zap className="w-4 h-4" />
              <span>Buy Now • ${((product.price || 0) * quantity).toFixed(2)}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Similar Products (Content-Based ML Model) */}
      <section className="pt-6">
        <div className="flex items-center space-x-3 mb-6 pb-3 border-b border-slate-200">
          <div className="p-2 rounded-xl bg-amber-50 text-amber-600 border border-amber-200">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Similar Products</h2>
            <p className="text-xs text-slate-500">
              Generated via TF-IDF item semantic representations & cosine similarity
            </p>
          </div>
        </div>

        <ProductGrid
          products={similarProducts}
          loading={loadingSimilar}
          emptyTitle="No similar products"
          emptyMessage="No direct TF-IDF matches found for this catalog item."
          onToast={showToast}
          skeletonCount={4}
        />
      </section>
    </div>
  );
};

export default ProductDetails;
