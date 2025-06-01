import axios from 'axios';

// Get API URL from environment variable
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create an axios instance with default configuration
const axiosInstance = axios.create({
  baseURL: API_URL,
  withCredentials: true, // Include cookies in cross-site requests
});

// Add a request interceptor to add the ngrok-skip-browser-warning header to all requests
axiosInstance.interceptors.request.use(
  config => {
    // Add the header to skip ngrok browser warning
    config.headers = {
      ...config.headers,
      'ngrok-skip-browser-warning': 'true',
      // Add additional headers that might help with CORS and ngrok
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    };

    // Log the request for debugging
    console.log('Making request to:', config.url, 'with headers:', config.headers);

    return config;
  },
  error => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add a response interceptor to log responses and check for ngrok warning page
axiosInstance.interceptors.response.use(
  response => {
    console.log('Response from:', response.config.url, 'status:', response.status);
    return response;
  },
  error => {
    console.error('Response error:', error);

    // Check if the error response contains the ngrok warning page HTML
    if (error.response && error.response.data && typeof error.response.data === 'string' && 
        error.response.data.includes('ngrok')) {
      console.error('Received ngrok warning page instead of API response. Check ngrok-skip-browser-warning header.');
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
