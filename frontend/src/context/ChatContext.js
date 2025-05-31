import React, { createContext, useState, useEffect, useContext, useRef } from 'react';
import axios from 'axios';
import { AuthContext } from './AuthContext';

export const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const { currentUser, isAuthenticated, getAuthHeader } = useContext(AuthContext);
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [leader, setLeader] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [activeRound, setActiveRound] = useState(null);
  
  const socketRef = useRef(null);
  
  // API URL from environment variable
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

  // Connect to WebSocket when authenticated
  useEffect(() => {
    if (isAuthenticated && currentUser) {
      connectWebSocket();
      
      // Fetch initial data
      fetchChatMessages();
      fetchChatUsers();
      fetchLeader();
      fetchActiveRound();
      
      return () => {
        // Disconnect WebSocket on unmount
        if (socketRef.current) {
          socketRef.current.close();
        }
      };
    }
  }, [isAuthenticated, currentUser]);

  // Connect to WebSocket
  const connectWebSocket = () => {
    const token = localStorage.getItem('token');
    if (!token || !currentUser) return;
    
    const socket = new WebSocket(`${WS_URL}/ws/${currentUser.id}`);
    
    socket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };
    
    socket.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      
      // Attempt to reconnect after a delay
      setTimeout(() => {
        if (isAuthenticated && currentUser) {
          connectWebSocket();
        }
      }, 3000);
    };
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
    
    socketRef.current = socket;
  };

  // Handle WebSocket messages
  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'chat_message':
        setMessages(prevMessages => [
          {
            id: Date.now(), // Temporary ID for new messages
            user_id: data.user_id,
            username: data.username,
            content: data.content,
            timestamp: data.timestamp
          },
          ...prevMessages
        ]);
        break;
        
      case 'user_status':
        // Refresh user list when a user connects or disconnects
        fetchChatUsers();
        break;
        
      case 'leader_assigned':
        setLeader({
          id: data.leader_id,
          screen_name: data.leader_name
        });
        break;
        
      case 'round_started':
        setActiveRound({
          id: data.round_id,
          timestamp: data.timestamp
        });
        // Redirect to game page will be handled by the component
        break;
        
      case 'round_ended':
        setActiveRound(null);
        // Refresh user list
        fetchChatUsers();
        // Refresh leader
        fetchLeader();
        break;
        
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  // Fetch chat messages
  const fetchChatMessages = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/chat/messages`, {
        headers: getAuthHeader()
      });
      
      setMessages(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch chat messages:', error);
      setError('Failed to load chat messages. Please try again.');
      setLoading(false);
    }
  };

  // Fetch chat room users
  const fetchChatUsers = async () => {
    try {
      const response = await axios.get(`${API_URL}/chat/users`, {
        headers: getAuthHeader()
      });
      
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch chat users:', error);
      setError('Failed to load chat users. Please try again.');
    }
  };

  // Fetch leader
  const fetchLeader = async () => {
    try {
      const response = await axios.get(`${API_URL}/chat/leader`, {
        headers: getAuthHeader()
      });
      
      setLeader(response.data);
    } catch (error) {
      console.error('Failed to fetch leader:', error);
      setError('Failed to load leader information. Please try again.');
    }
  };

  // Fetch active round
  const fetchActiveRound = async () => {
    try {
      const response = await axios.get(`${API_URL}/game/rounds/active`, {
        headers: getAuthHeader()
      });
      
      setActiveRound(response.data);
    } catch (error) {
      console.error('Failed to fetch active round:', error);
      // No need to set error, as there might not be an active round
      setActiveRound(null);
    }
  };

  // Send a chat message
  const sendMessage = async (content) => {
    try {
      if (!content.trim()) return;
      
      await axios.post(`${API_URL}/chat/messages`, {
        user_id: currentUser.id,
        content: content
      }, {
        headers: getAuthHeader()
      });
      
      // The message will be added to the state via WebSocket
    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Failed to send message. Please try again.');
    }
  };

  // Start a new game round (leader only)
  const startRound = async () => {
    try {
      if (!currentUser || currentUser.role !== 'LEADER') {
        throw new Error('Only the leader can start a round');
      }
      
      // Send WebSocket message to start round
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: 'start_round'
        }));
      }
      
      return true;
    } catch (error) {
      console.error('Failed to start round:', error);
      setError('Failed to start round. Please try again.');
      return false;
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        users,
        leader,
        loading,
        error,
        isConnected,
        activeRound,
        sendMessage,
        startRound,
        fetchChatMessages,
        fetchChatUsers,
        fetchLeader,
        fetchActiveRound
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};