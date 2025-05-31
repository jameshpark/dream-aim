import React, { useState } from 'react';
import styled from 'styled-components';
import { FaUser, FaCheck, FaTimes } from 'react-icons/fa';

const BuddyListContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const BuddyItem = styled.div`
  display: flex;
  align-items: center;
  padding: 12px 15px;
  background-color: ${props => props.isGuessMode ? '#f5f5f5' : 'var(--window-bg)'};
  border: 2px solid ${props => props.isGuessMode ? 'var(--primary-color)' : 'var(--window-border)'};
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background-color: ${props => props.isGuessMode ? '#e0e0e0' : '#f5f5f5'};
    transform: translateY(-2px);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  }
`;

const BuddyIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 20px;
`;

const BuddyInfo = styled.div`
  flex: 1;
`;

const BuddyName = styled.div`
  font-weight: bold;
  font-size: 18px;
  margin-bottom: 5px;
`;

const BuddyDetails = styled.div`
  font-size: 14px;
  color: #666;
`;

const GuessControls = styled.div`
  display: flex;
  gap: 10px;
  margin-top: 20px;
`;

const GuessButton = styled.button`
  flex: 1;
  padding: 10px;
  font-family: 'VT323', monospace;
  font-size: 16px;
  border: 2px outset var(--button-border);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;

  &:first-child {
    background-color: #f44336;
    color: white;

    &:hover {
      background-color: #d32f2f;
    }
  }

  &:last-child {
    background-color: #4caf50;
    color: white;

    &:hover {
      background-color: #388e3c;
    }
  }

  &:active {
    border-style: inset;
    transform: translateY(1px);
  }
`;

const GuessTitle = styled.h3`
  text-align: center;
  margin-bottom: 15px;
  color: var(--primary-color);
`;

const BuddyList = ({ 
  buddies, 
  onBuddyClick, 
  isGuessMode, 
  onGuessSubmit, 
  onCancelGuess 
}) => {
  const [selectedBuddy, setSelectedBuddy] = useState(null);

  const handleBuddyClick = (buddy) => {
    if (isGuessMode) {
      setSelectedBuddy(buddy.id === selectedBuddy ? null : buddy.id);
    } else {
      onBuddyClick(buddy.id);
    }
  };

  const handleSubmitGuess = () => {
    if (selectedBuddy) {
      onGuessSubmit(selectedBuddy);
    }
  };

  return (
    <BuddyListContainer>
      {isGuessMode && (
        <GuessTitle>Select your secret admirer</GuessTitle>
      )}

      {buddies.map(buddy => (
        <BuddyItem 
          key={buddy.id} 
          onClick={() => handleBuddyClick(buddy)}
          isGuessMode={isGuessMode}
          isSelected={selectedBuddy === buddy.id}
          style={{
            borderColor: selectedBuddy === buddy.id ? 'var(--primary-color)' : '',
            borderWidth: selectedBuddy === buddy.id ? '3px' : ''
          }}
        >
          <BuddyIcon>
            <FaUser />
          </BuddyIcon>
          <BuddyInfo>
            <BuddyName>{buddy.name}</BuddyName>
            <BuddyDetails>
              {buddy.gender}, {buddy.sexual_orientation}, {buddy.gender_identity}
            </BuddyDetails>
          </BuddyInfo>
        </BuddyItem>
      ))}

      {isGuessMode && (
        <GuessControls>
          <GuessButton onClick={onCancelGuess}>
            <FaTimes /> Cancel
          </GuessButton>
          <GuessButton 
            onClick={handleSubmitGuess}
            disabled={!selectedBuddy}
            style={{ opacity: !selectedBuddy ? 0.5 : 1 }}
          >
            <FaCheck /> Confirm Guess
          </GuessButton>
        </GuessControls>
      )}
    </BuddyListContainer>
  );
};

export default BuddyList;
