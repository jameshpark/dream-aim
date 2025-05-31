import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { AuthContext } from '../../context/AuthContext';
import { ChatContext } from '../../context/ChatContext';
import { GameContext } from '../../context/GameContext';
import BuddyList from './BuddyList';

const GameWindow = styled.div`
  background-color: var(--window-bg);
  border: 2px solid var(--window-border);
  border-radius: 5px;
  box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 800px;
  height: 600px;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  @media (max-width: 768px) {
    max-width: 100%;
    height: 100vh;
    border-radius: 0;
    box-shadow: none;
  }
`;

const GameHeader = styled.div`
  background-color: var(--header-bg);
  color: var(--header-text);
  padding: 8px 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const GameTitle = styled.h2`
  font-size: 18px;
  margin: 0;
`;

const HeaderButtons = styled.div`
  display: flex;
  gap: 10px;
`;

const HeaderButton = styled.button`
  background-color: var(--button-bg);
  border: 1px solid var(--button-border);
  color: var(--button-text);
  font-size: 14px;
  padding: 2px 5px;
  cursor: pointer;
`;

const GameContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 15px;
  overflow-y: auto;
`;

const GameInstructions = styled.div`
  margin-bottom: 20px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 5px;
  border: 1px solid #ddd;
`;

const GuessButton = styled.button`
  background-color: var(--primary-color);
  color: white;
  border: 2px outset var(--button-border);
  padding: 10px 20px;
  font-family: 'VT323', monospace;
  font-size: 18px;
  cursor: pointer;
  margin-top: 20px;
  width: 100%;
  max-width: 300px;
  align-self: center;

  &:hover {
    background-color: #0055aa;
  }

  &:active {
    border-style: inset;
    transform: translateY(1px);
  }
`;

const LoadingMessage = styled.div`
  text-align: center;
  padding: 20px;
  font-style: italic;
`;

const ErrorMessage = styled.div`
  color: var(--error-color);
  text-align: center;
  padding: 20px;
`;

const GameRound = () => {
  const navigate = useNavigate();
  const { currentUser, isAuthenticated } = useContext(AuthContext);
  const { activeRound } = useContext(ChatContext);
  const { 
    buddies, 
    loading, 
    error, 
    fetchBuddies,
    makeGuess,
    returnToLobby
  } = useContext(GameContext);

  const [showGuessModal, setShowGuessModal] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  // Redirect if no active round
  useEffect(() => {
    if (!activeRound) {
      navigate('/chat');
    }
  }, [activeRound, navigate]);

  // Fetch buddies when component mounts
  useEffect(() => {
    if (isAuthenticated && currentUser && activeRound) {
      fetchBuddies();
    }
  }, [isAuthenticated, currentUser, activeRound]);

  const handleBuddyClick = (buddyId) => {
    navigate(`/buddy/${buddyId}`);
  };

  const handleMakeGuess = () => {
    setShowGuessModal(true);
  };

  const handleGuessSubmit = async (buddyId) => {
    const result = await makeGuess(buddyId);
    if (result) {
      navigate('/result');
    }
  };

  const handleBackToChat = async () => {
    await returnToLobby();
    navigate('/chat');
  };

  return (
    <GameWindow>
      <GameHeader>
        <GameTitle>Dream AIM - Secret Admirer</GameTitle>
        <HeaderButtons>
          <HeaderButton onClick={handleBackToChat}>Back to Chat</HeaderButton>
        </HeaderButtons>
      </GameHeader>

      <GameContent>
        <GameInstructions>
          <h3>Find Your Secret Admirer!</h3>
          <p>One of these buddies is your secret admirer. Chat with them to gather clues and figure out who it is!</p>
          <p>When you're ready, click "Make a Guess" to select your secret admirer.</p>
        </GameInstructions>

        {loading ? (
          <LoadingMessage>Loading buddies...</LoadingMessage>
        ) : error ? (
          <ErrorMessage>{error}</ErrorMessage>
        ) : (
          <>
            <BuddyList 
              buddies={buddies} 
              onBuddyClick={handleBuddyClick} 
              isGuessMode={showGuessModal}
              onGuessSubmit={handleGuessSubmit}
              onCancelGuess={() => setShowGuessModal(false)}
            />

            {!showGuessModal && (
              <GuessButton onClick={handleMakeGuess}>
                Make a Guess
              </GuessButton>
            )}
          </>
        )}
      </GameContent>
    </GameWindow>
  );
};

export default GameRound;
