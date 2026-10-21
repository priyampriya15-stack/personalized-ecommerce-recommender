import api from './api';

export const cartService = {
  async getCart() {
    return await api.get('/cart');
  },

  async addToCart(productId, quantity = 1) {
    return await api.post('/cart/items', {
      product_id: productId,
      quantity,
    });
  },

  async removeFromCart(productId) {
    return await api.delete(`/cart/items/${productId}`);
  },

  async checkout() {
    return await api.post('/cart/checkout');
  },
};

export default cartService;
