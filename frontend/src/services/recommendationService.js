import api from './api';

export const recommendationService = {
  async getPopularRecommendations(params = {}) {
    return await api.get('/recommendations/popular', { params });
  },

  async getHybridRecommendations(userId = 'me', params = {}) {
    return await api.get(`/recommendations/${userId || 'me'}/hybrid`, { params });
  },

  async getCollaborativeRecommendations(userId = 'me', params = {}) {
    return await api.get(`/recommendations/${userId || 'me'}/collaborative`, { params });
  },

  async getContentBasedRecommendations(userId = 'me', params = {}) {
    return await api.get(`/recommendations/${userId || 'me'}/content-based`, { params });
  },
};

export default recommendationService;
