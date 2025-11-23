import axios from 'axios';

const client = axios.create({
  // Default to the local FastAPI dev server when no env var is provided.
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
  withCredentials: true
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
export const put = (url, payload, config = {}) => client.put(url, payload, config);
export const patch = (url, payload, config = {}) => client.patch(url, payload, config);
export const del = (url, config = {}) => client.delete(url, config);

// Authentication API
export const login = async (credentials) => {
  const response = await post('/auth/login', credentials);
  return response.data;
};

export const getCurrentUser = async () => {
  return await get('/auth/me');
};

export const logout = () => {
  // Clear any local state if needed
  // The session cookie will be cleared on the next login
  return Promise.resolve();
};

// Setup API
export const getSetupStatus = async () => {
  const response = await get('/auth/setup-status');
  return response.data;
};

export const setupApplicationManager = async (data) => {
  const response = await post('/auth/application-manager-setup', data);
  return response.data;
};

// Institution API
export const getInstitutions = () => get('/institutions/');
export const createInstitution = (data) => post('/institutions/', data);
export const updateInstitution = (id, data) => put(`/institutions/${id}`, data);
export const deleteInstitution = (id) => del(`/institutions/${id}`);

// Department API
export const getDepartments = (institutionId = null) => {
  const params = institutionId ? { institution_id: institutionId } : {};
  return get('/departments/', { params });
};
export const createDepartment = (data) => post('/departments/', data);
export const updateDepartment = (id, data) => put(`/departments/${id}`, data);
export const deleteDepartment = (id) => del(`/departments/${id}`);

// Role API
export const getRoles = () => get('/roles/');
