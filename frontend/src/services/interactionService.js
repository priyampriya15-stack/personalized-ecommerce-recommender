import api from './api';

export const interactionService = {
  async recordInteraction({ productId, interactionType, rating = null }) {
    return await api.post('/interactions', {
      product_id: productId,
      interaction_type: interactionType,
      rating,
    });
  },

  async getUserHistory(userId, type = null, limit = 50) {
    const params = { limit };
    if (type) params.type = type;
    return await api.get(`/users/${userId}/history`, { params });
  },

  async updatePreferences(categories) {
    return await api.post('/users/preferences', { categories });
  },
};

export default interactionService;
