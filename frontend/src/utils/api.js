import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const apiCall = async (endpoint, method = 'GET', data = null, config = {}) => {
  try {
    const response = await api({
      url: endpoint,
      method,
      data,
      ...config
    });
    return response.data;
  } catch (error) {
    console.error('API Call Error:', error);
    throw error;
  }
};

export const uploadFile = async (endpoint, file, progressCallback = null) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api({
      url: endpoint,
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressCallback) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          progressCallback(percentCompleted);
        }
      },
    });

    return response.data;
  } catch (error) {
    console.error('File Upload Error:', error);
    throw error;
  }
};

export const downloadFile = async (endpoint, filename) => {
  try {
    const response = await api({
      url: endpoint,
      method: 'GET',
      responseType: 'blob',
    });

    // Create blob link to download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('File Download Error:', error);
    throw error;
  }
};

export default api;