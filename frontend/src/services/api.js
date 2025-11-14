import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 10000
});

client.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      console.error('API error', error.response.data);
    }
    return Promise.reject(error);
  }
);

export const get = (url, config = {}) => client.get(url, config);
export const post = (url, payload, config = {}) => client.post(url, payload, config);
export const patch = (url, payload, config = {}) => client.patch(url, payload, config);
export const del = (url, config = {}) => client.delete(url, config);
