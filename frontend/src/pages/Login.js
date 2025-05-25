import React, { useState } from 'react';
import axios from 'axios';

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!username.trim()) {
      setError('Username is required');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      // Create a new user or get existing user
      const response = await axios.post('/api/users/', { username });
      
      // Call the onLogin function with the user data
      onLogin(response.data);
    } catch (error) {
      console.error('Login error:', error);
      setError(
        error.response?.data?.detail || 
        'An error occurred during login. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-screen aim-window">
      <div className="aim-header">
        <div>Dream AIM</div>
        <div className="aim-header-buttons">
          <div className="aim-header-button aim-minimize"></div>
          <div className="aim-header-button aim-maximize"></div>
          <div className="aim-header-button aim-close"></div>
        </div>
      </div>
      <div className="aim-content">
        <div className="login-logo">Dream AIM</div>
        <form className="login-form" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Enter your username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Signing In...' : 'Sign In'}
          </button>
          {error && <div className="error-message">{error}</div>}
        </form>
        <div className="login-info">
          <p>Welcome to Dream AIM!</p>
          <p>Enter a username to start playing Dream Phone.</p>
        </div>
      </div>
    </div>
  );
};

export default Login;