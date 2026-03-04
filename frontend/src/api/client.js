import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_BASE_HTTP_URL || 'http://127.0.0.1:8000/';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authApi = {
  login: (username, password) =>
    api.post('login/', { username, password }),

  signup: (formData) =>
    api.post('signup/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  googleAuth: (token, mode) =>
    api.post('google-auth/', { token, mode }),
};

export default api;
