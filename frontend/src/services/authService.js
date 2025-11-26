import api from './api';

const authService = {
  initiateLogin: async (provider) => {
    try {
      const response = await api.post(`/auth/login/${provider}`);
      return response.data.redirect_url;
    } catch (error) {
      console.error(`Error initiating ${provider} login:`, error);
      throw error;
    }
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.error('Error logging out:', error);
      throw error;
    }
  },

  refreshToken: async () => {
    try {
      const response = await api.post('/auth/refresh');
      return response.data.access_token;
    } catch (error) {
      console.error('Error refreshing token:', error);
      throw error;
    }
  }
};

export default authService;
