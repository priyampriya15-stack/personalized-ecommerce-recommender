import api from './api';

export const authService = {
  async register({ name, email, password, categories = [] }) {
    return await api.post('/auth/register', { name, email, password, categories });
  },

  async login({ email, password }) {
    return await api.post('/auth/login', { email, password });
  },

  async getCurrentUser() {
    return await api.get('/auth/me');
  },
};

export default authService;
