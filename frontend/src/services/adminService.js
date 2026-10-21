import api from './api';

export const adminService = {
  async getAnalytics() {
    return await api.get('/admin/analytics');
  },

  async getModelMetrics() {
    return await api.get('/admin/model-metrics');
  },

  async updateRecommendationSettings(alpha) {
    return await api.put('/admin/recommendation-settings', { alpha });
  },
};

export default adminService;
