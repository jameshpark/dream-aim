import React, { useContext } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthContext } from './context/AuthContext';
import SignOn from './components/auth/SignOn';
import ChatRoom from './components/chat/ChatRoom';
import GameRound from './components/game/GameRound';
import BuddyChat from './components/game/BuddyChat';
import GuessResult from './components/game/GuessResult';
import styled from 'styled-components';

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  background-color: #f0f0f0;
`;

// Protected route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useContext(AuthContext);
  
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  
  return children;
};

function App() {
  return (
    <AppContainer>
      <Routes>
        <Route path="/" element={<SignOn />} />
        <Route 
          path="/chat" 
          element={
            <ProtectedRoute>
              <ChatRoom />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/game" 
          element={
            <ProtectedRoute>
              <GameRound />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/buddy/:buddyId" 
          element={
            <ProtectedRoute>
              <BuddyChat />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/result" 
          element={
            <ProtectedRoute>
              <GuessResult />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </AppContainer>
  );
}

export default App;