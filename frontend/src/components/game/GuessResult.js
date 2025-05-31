import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import Confetti from 'react-confetti';
import { AuthContext } from '../../context/AuthContext';
import { GameContext } from '../../context/GameContext';
import { FaHeart, FaArrowRight } from 'react-icons/fa';

const ResultWindow = styled.div`
  background-color: var(--window-bg);
  border: 2px solid var(--window-border);
  border-radius: 5px;
  box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 600px;
  padding: 30px;
  text-align: center;
  position: relative;
  overflow: hidden;
`;

const ResultTitle = styled.h2`
  font-size: 28px;
  margin-bottom: 20px;
  color: ${props => props.correct ? 'var(--success-color)' : 'var(--error-color)'};
`;

const ResultMessage = styled.p`
  font-size: 18px;
  margin-bottom: 30px;
`;

const HeartIcon = styled.div`
  font-size: 60px;
  color: ${props => props.correct ? 'var(--success-color)' : 'var(--error-color)'};
  margin: 20px 0;
  animation: ${props => props.correct ? 'pulse 1.5s infinite' : 'none'};

  @keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.2); }
    100% { transform: scale(1); }
  }
`;

const RevealButton = styled.button`
  background-color: var(--primary-color);
  color: white;
  border: 2px outset var(--button-border);
  padding: 10px 20px;
  font-family: 'VT323', monospace;
  font-size: 18px;
  cursor: pointer;
  margin: 20px 0;

  &:hover {
    background-color: #0055aa;
  }

  &:active {
    border-style: inset;
    transform: translateY(1px);
  }
`;

const ReturnButton = styled.button`
  background-color: var(--button-bg);
  border: 2px outset var(--button-border);
  color: var(--button-text);
  padding: 10px 20px;
  font-family: 'VT323', monospace;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin: 0 auto;

  &:hover {
    background-color: #e0e0e0;
  }

  &:active {
    border-style: inset;
    transform: translateY(1px);
  }
`;

const SecretAdmirerInfo = styled.div`
  margin: 20px 0;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 5px;
  border: 1px solid #ddd;
  text-align: left;
`;

const AdmirerName = styled.h3`
  margin: 0 0 10px 0;
  color: var(--primary-color);
`;

const AdmirerDetails = styled.p`
  margin: 5px 0;
  font-size: 16px;
`;

const GuessResult = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useContext(AuthContext);
  const { guessResult, buddies, returnToLobby } = useContext(GameContext);
  const [showAdmirer, setShowAdmirer] = useState(false);
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  });

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  // Redirect if no guess result
  useEffect(() => {
    if (!guessResult) {
      navigate('/game');
    }
  }, [guessResult, navigate]);

  // Update window size for confetti
  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleRevealAdmirer = () => {
    setShowAdmirer(true);
  };

  const handleReturnToLobby = async () => {
    await returnToLobby();
    navigate('/chat');
  };

  // Get the secret admirer name directly from the guessResult
  const secretAdmirerName = guessResult?.secret_admirer || null;

  // Find the secret admirer buddy if available
  const secretAdmirerBuddy = secretAdmirerName && buddies.length > 0
    ? buddies.find(b => b.name === secretAdmirerName) 
    : null;

  const isCorrect = guessResult?.correct;

  return (
    <ResultWindow>
      {isCorrect && (
        <Confetti
          width={windowSize.width}
          height={windowSize.height}
          recycle={false}
          numberOfPieces={500}
          gravity={0.2}
        />
      )}

      <ResultTitle correct={isCorrect}>
        {isCorrect ? 'Congratulations!' : 'Sorry!'}
      </ResultTitle>

      <HeartIcon correct={isCorrect}>
        <FaHeart />
      </HeartIcon>

      <ResultMessage>
        {isCorrect 
          ? "You've found your secret admirer! They've been waiting for you all along!"
          : "That's not your secret admirer. Don't worry, you'll find love next time!"}
      </ResultMessage>

      {!isCorrect && !showAdmirer && (
        <RevealButton onClick={handleRevealAdmirer}>
          Your secret admirer was...
        </RevealButton>
      )}

      {(!isCorrect && showAdmirer) && (
        <SecretAdmirerInfo>
          {secretAdmirerBuddy ? (
            <>
              <AdmirerName>{secretAdmirerBuddy.name}</AdmirerName>
              <AdmirerDetails>
                <strong>Gender:</strong> {secretAdmirerBuddy.gender}
              </AdmirerDetails>
              <AdmirerDetails>
                <strong>Sexual Orientation:</strong> {secretAdmirerBuddy.sexual_orientation}
              </AdmirerDetails>
              <AdmirerDetails>
                <strong>Gender Identity:</strong> {secretAdmirerBuddy.gender_identity}
              </AdmirerDetails>
              <AdmirerDetails>
                <strong>Video Games:</strong> {secretAdmirerBuddy.video_games}
              </AdmirerDetails>
              <AdmirerDetails>
                <strong>TV Shows:</strong> {secretAdmirerBuddy.tv_shows}
              </AdmirerDetails>
              <AdmirerDetails>
                <strong>Music Artists:</strong> {secretAdmirerBuddy.music_artists}
              </AdmirerDetails>
              <AdmirerDetails>
                <strong>Pet Preference:</strong> {secretAdmirerBuddy.pet_preference}
              </AdmirerDetails>
            </>
          ) : (
            <AdmirerName>{secretAdmirerName}</AdmirerName>
          )}
        </SecretAdmirerInfo>
      )}

      <ReturnButton onClick={handleReturnToLobby}>
        Return to Lobby <FaArrowRight />
      </ReturnButton>
    </ResultWindow>
  );
};

export default GuessResult;
