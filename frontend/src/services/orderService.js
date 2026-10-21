import api from './api';

export const orderService = {
  async getOrderQuote(data = {}) {
    return await api.post('/orders/quote', data);
  },

  async createOrder(data = {}) {
    return await api.post('/orders', data);
  },

  async getUserOrders() {
    return await api.get('/orders');
  },

  async buyNow(productId, quantity = 1) {
    return await api.post('/orders/buy-now', { product_id: productId, quantity });
  },

  async getOrderById(orderId) {
    return await api.get(`/orders/${orderId}`);
  },

  async cancelOrder(orderId) {
    return await api.post(`/orders/${orderId}/cancel`);
  },
};

export default orderService;

