import api from './api';

export const productService = {
  async getProducts(params = {}) {
    return await api.get('/products', { params });
  },

  async getProductById(productId) {
    return await api.get(`/products/${productId}`);
  },

  async searchProducts(query, page = 1, limit = 20) {
    return await api.get('/products/search', {
      params: { q: query, page, limit },
    });
  },

  async getCategories() {
    return await api.get('/products/categories');
  },

  async getSimilarProducts(productId, limit = 6) {
    return await api.get(`/products/${productId}/similar`, {
      params: { limit },
    });
  },
};

export default productService;
