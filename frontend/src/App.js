import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import WaitingRoom from './pages/WaitingRoom';
import Game from './pages/Game';
import './styles/index.css';

function App() {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check if user is already logged in
  useEffect(() => {
    const storedUser = localStorage.getItem('dreamAimUser');
    if (storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Error parsing stored user:', error);
        localStorage.removeItem('dreamAimUser');
      }
    }
  }, []);

  // Handle login
  const handleLogin = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
    localStorage.setItem('dreamAimUser', JSON.stringify(userData));
  };

  // Handle logout
  const handleLogout = () => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('dreamAimUser');
  };

  return (
    <Router>
      <div className="app">
        <Routes>
          <Route 
            path="/" 
            element={
              isAuthenticated ? 
                <Navigate to="/waiting-room" /> : 
                <Login onLogin={handleLogin} />
            } 
          />
          <Route 
            path="/waiting-room" 
            element={
              isAuthenticated ? 
                <WaitingRoom user={user} onLogout={handleLogout} /> : 
                <Navigate to="/" />
            } 
          />
          <Route 
            path="/game/:gameId" 
            element={
              isAuthenticated ? 
                <Game user={user} onLogout={handleLogout} /> : 
                <Navigate to="/" />
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;