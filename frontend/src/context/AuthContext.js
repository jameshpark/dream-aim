import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // API URL from environment variable
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Check if user is already authenticated on component mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      checkAuthStatus(token);
    } else {
      setLoading(false);
    }
  }, []);

  // Check authentication status
  const checkAuthStatus = async (token) => {
    try {
      const response = await axios.get(`${API_URL}/users/me`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      setCurrentUser(response.data);
      setIsAuthenticated(true);
      setLoading(false);
    } catch (error) {
      console.error('Authentication check failed:', error);
      localStorage.removeItem('token');
      setIsAuthenticated(false);
      setLoading(false);
    }
  };

  // Sign in function
  const signIn = async (screenName, password) => {
    try {
      setError(null);
      setLoading(true);
      
      const response = await axios.post(`${API_URL}/users/signin`, {
        screen_name: screenName,
        password: password
      });
      
      const { access_token } = response.data;
      
      // Store token in localStorage
      localStorage.setItem('token', access_token);
      
      // Get user data
      await checkAuthStatus(access_token);
      
      return true;
    } catch (error) {
      console.error('Sign in failed:', error);
      setError(error.response?.data?.detail || 'Sign in failed. Please try again.');
      setLoading(false);
      return false;
    }
  };

  // Sign up function
  const signUp = async (screenName, password) => {
    try {
      setError(null);
      setLoading(true);
      
      const response = await axios.post(`${API_URL}/users/`, {
        screen_name: screenName,
        password: password
      });
      
      // After successful registration, sign in
      return await signIn(screenName, password);
    } catch (error) {
      console.error('Sign up failed:', error);
      setError(error.response?.data?.detail || 'Sign up failed. Please try again.');
      setLoading(false);
      return false;
    }
  };

  // Sign out function
  const signOut = async () => {
    try {
      const token = localStorage.getItem('token');
      
      if (token) {
        await axios.post(`${API_URL}/users/signout`, {}, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
      }
    } catch (error) {
      console.error('Sign out API call failed:', error);
    } finally {
      // Clear local storage and state regardless of API success
      localStorage.removeItem('token');
      setCurrentUser(null);
      setIsAuthenticated(false);
    }
  };

  // Get auth header for API requests
  const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        isAuthenticated,
        loading,
        error,
        signIn,
        signUp,
        signOut,
        getAuthHeader
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};