import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router } from 'react-router-dom';
import App from './App';
import { AuthProvider } from './context/AuthContext';
import { ChatProvider } from './context/ChatContext';
import { GameProvider } from './context/GameContext';
import './styles/index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Router>
      <AuthProvider>
        <ChatProvider>
          <GameProvider>
            <App />
          </GameProvider>
        </ChatProvider>
      </AuthProvider>
    </Router>
  </React.StrictMode>
);