import axios from 'axios';

// Get the API base URL from Vite's environment variables, with a fallback for local development
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // You can add other default headers here, like Authorization tokens
  },
});

// Optional: Add a request interceptor for things like adding auth tokens dynamically
// apiClient.interceptors.request.use(
//   (config) => {
//     const token = localStorage.getItem('accessToken'); // Example: get token from local storage
//     if (token) {
//       config.headers['Authorization'] = `Bearer ${token}`;
//     }
//     return config;
//   },
//   (error) => {
//     return Promise.reject(error);
//   }
// );

// Optional: Add a response interceptor for global error handling or data transformation
// apiClient.interceptors.response.use(
//   (response) => {
//     // Any status code that lie within the range of 2xx cause this function to trigger
//     // Do something with response data
//     return response;
//   },
//   (error) => {
//     // Any status codes that falls outside the range of 2xx cause this function to trigger
//     // Do something with response error
//     // For example, redirect to login if 401 Unauthorized
//     if (error.response && error.response.status === 401) {
//       // Handle unauthorized access, e.g., redirect to login page
//       console.error('Unauthorized, redirecting to login...');
//       // window.location.href = '/login';
//     }
//     return Promise.reject(error);
//   }
// );

export default apiClient; 