const isBrowser = typeof window !== 'undefined';

const storage = isBrowser ? window.localStorage : null;

export const appParams = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',

  getToken: () => {
    if (!isBrowser) return null;
    return storage.getItem('access_token');
  },

  setToken: (token) => {
    if (!isBrowser) return;
    storage.setItem('access_token', token);
  },

  removeToken: () => {
    if (!isBrowser) return;
    storage.removeItem('access_token');
  }
};
