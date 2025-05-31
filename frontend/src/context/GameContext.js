import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from './AuthContext';
import { ChatContext } from './ChatContext';

export const GameContext = createContext();

export const GameProvider = ({ children }) => {
  const { currentUser, isAuthenticated, getAuthHeader } = useContext(AuthContext);
  const { activeRound } = useContext(ChatContext);

  const [buddies, setBuddies] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [conversationMessages, setConversationMessages] = useState([]);
  const [guessResult, setGuessResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isBuddyTyping, setIsBuddyTyping] = useState(false);

  // API URL from environment variable
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';


  // Fetch conversations when in an active round
  useEffect(() => {
    if (isAuthenticated && currentUser && activeRound) {
      fetchConversations();
    }
  }, [isAuthenticated, currentUser, activeRound]);

  // Fetch buddies
  const fetchBuddies = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/game/buddies`, {
        headers: getAuthHeader()
      });

      setBuddies(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch buddies:', error);
      setError('Failed to load buddies. Please try again.');
      setLoading(false);
    }
  };

  // Fetch conversations
  const fetchConversations = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/chat/conversations`, {
        headers: getAuthHeader()
      });

      setConversations(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
      setError('Failed to load conversations. Please try again.');
      setLoading(false);
    }
  };

  // Start a conversation with a buddy
  const startConversation = async (buddyId) => {
    try {
      if (!activeRound) {
        throw new Error('No active round');
      }

      // Check if conversation already exists
      const existingConversation = conversations.find(
        conv => conv.buddy_id === buddyId && conv.round_id === activeRound.id
      );

      if (existingConversation) {
        setCurrentConversation(existingConversation);
        await fetchConversationMessages(existingConversation.id);
        return existingConversation;
      }

      // Create a new conversation
      const response = await axios.post(`${API_URL}/chat/conversations`, {
        user_id: currentUser.id,
        buddy_id: buddyId,
        round_id: activeRound.id
      }, {
        headers: getAuthHeader()
      });

      const newConversation = response.data;
      setConversations(prev => [...prev, newConversation]);
      setCurrentConversation(newConversation);

      return newConversation;
    } catch (error) {
      console.error('Failed to start conversation:', error);
      setError('Failed to start conversation. Please try again.');
      return null;
    }
  };

  // Fetch conversation messages
  const fetchConversationMessages = async (conversationId) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/chat/conversations/${conversationId}/messages`, {
        headers: getAuthHeader()
      });

      setConversationMessages(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch conversation messages:', error);
      setError('Failed to load conversation messages. Please try again.');
      setLoading(false);
    }
  };

  // Send a message to a buddy
  const sendMessageToBuddy = async (conversationId, content) => {
    try {
      if (!content.trim()) return;

      const response = await axios.post(`${API_URL}/chat/conversations/${conversationId}/messages`, {
        sender_type: 'user',
        content: content
      }, {
        headers: getAuthHeader()
      });

      // Add the message to the state
      setConversationMessages(prev => [...prev, response.data]);

      // Show typing indicator
      setIsBuddyTyping(true);

      // Fetch updated messages after a random delay between 1-3 seconds to get the buddy's response
      const randomDelay = Math.floor(Math.random() * 2000) + 1000; // Random delay between 1-3 seconds
      setTimeout(() => {
        fetchConversationMessages(conversationId);
        setIsBuddyTyping(false);
      }, randomDelay);

      return response.data;
    } catch (error) {
      console.error('Failed to send message to buddy:', error);
      setError('Failed to send message. Please try again.');
      setIsBuddyTyping(false);
      return null;
    }
  };

  // Make a guess
  const makeGuess = async (buddyId) => {
    try {
      if (!activeRound) {
        throw new Error('No active round');
      }

      const response = await axios.post(`${API_URL}/game/guess/${buddyId}`, {}, {
        headers: getAuthHeader()
      });

      setGuessResult(response.data.data);
      return response.data.data;
    } catch (error) {
      console.error('Failed to make guess:', error);
      setError('Failed to make guess. Please try again.');
      return null;
    }
  };

  // Return to lobby after making a guess
  const returnToLobby = async () => {
    try {
      await axios.post(`${API_URL}/game/return-to-lobby`, {}, {
        headers: getAuthHeader()
      });

      // Reset game state
      setCurrentConversation(null);
      setConversationMessages([]);
      setGuessResult(null);

      return true;
    } catch (error) {
      console.error('Failed to return to lobby:', error);
      setError('Failed to return to lobby. Please try again.');
      return false;
    }
  };

  return (
    <GameContext.Provider
      value={{
        buddies,
        conversations,
        currentConversation,
        conversationMessages,
        guessResult,
        loading,
        error,
        isBuddyTyping,
        fetchBuddies,
        fetchConversations,
        startConversation,
        fetchConversationMessages,
        sendMessageToBuddy,
        makeGuess,
        returnToLobby,
        setCurrentConversation
      }}
    >
      {children}
    </GameContext.Provider>
  );
};
