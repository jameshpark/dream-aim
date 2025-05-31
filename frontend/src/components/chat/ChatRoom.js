import React, { useState, useContext, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { AuthContext } from '../../context/AuthContext';
import { ChatContext } from '../../context/ChatContext';
import UserList from './UserList';
import ChatMessage from './ChatMessage';

const ChatWindow = styled.div`
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

const ChatHeader = styled.div`
  background-color: var(--header-bg);
  color: var(--header-text);
  padding: 8px 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const ChatTitle = styled.h2`
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

const ChatContent = styled.div`
  display: flex;
  flex: 1;
  overflow: hidden;
`;

const MainChat = styled.div`
  flex: 3;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--window-border);
`;

const ChatMessages = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background-color: var(--chat-bg);
  display: flex;
  flex-direction: column-reverse;
`;

const ChatInputArea = styled.div`
  padding: 10px;
  border-top: 1px solid var(--window-border);
  background-color: var(--window-bg);
`;

const ChatInputForm = styled.form`
  display: flex;
  gap: 10px;
`;

const ChatInput = styled.input`
  flex: 1;
  background-color: var(--input-bg);
  border: 2px inset var(--input-border);
  color: var(--input-text);
  padding: 8px 10px;
  font-family: 'VT323', monospace;
  font-size: 16px;
`;

const SendButton = styled.button`
  background-color: var(--button-bg);
  border: 2px outset var(--button-border);
  color: var(--button-text);
  padding: 8px 15px;
  font-family: 'VT323', monospace;
  font-size: 16px;
  cursor: pointer;
  white-space: nowrap;

  &:hover {
    background-color: #e0e0e0;
  }

  &:active {
    border-style: inset;
    transform: translateY(1px);
  }
`;

const Sidebar = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--buddy-list-bg);
`;

const SidebarHeader = styled.div`
  padding: 10px;
  border-bottom: 1px solid var(--window-border);
  font-weight: bold;
`;

const StartRoundButton = styled.button`
  background-color: var(--primary-color);
  color: white;
  border: 2px outset var(--button-border);
  padding: 8px 15px;
  font-family: 'VT323', monospace;
  font-size: 16px;
  cursor: pointer;
  margin-top: 10px;
  width: 100%;

  &:hover {
    background-color: #0055aa;
  }

  &:active {
    border-style: inset;
    transform: translateY(1px);
  }

  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
`;

const StatusMessage = styled.div`
  padding: 10px;
  text-align: center;
  color: ${props => props.isError ? 'var(--error-color)' : 'var(--text-color)'};
  font-style: italic;
`;

const ChatRoom = () => {
  const [message, setMessage] = useState('');
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  const { currentUser, isAuthenticated, signOut } = useContext(AuthContext);
  const { 
    messages, 
    users, 
    leader, 
    loading, 
    error, 
    isConnected,
    activeRound,
    sendMessage,
    startRound,
    fetchLeader,
    fetchChatUsers
  } = useContext(ChatContext);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  // Redirect if active round
  useEffect(() => {
    if (activeRound) {
      navigate('/game');
    }
  }, [activeRound, navigate]);

  // Periodically refresh leader and users list to ensure UI is up to date
  useEffect(() => {
    if (isAuthenticated && isConnected) {
      const interval = setInterval(() => {
        fetchLeader();
        fetchChatUsers();
      }, 5000); // Refresh every 5 seconds

      return () => clearInterval(interval);
    }
  }, [isAuthenticated, isConnected, fetchLeader, fetchChatUsers]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (message.trim()) {
      sendMessage(message);
      setMessage('');
    }
  };

  const handleStartRound = async () => {
    const success = await startRound();
    if (success) {
      navigate('/game');
    }
  };

  const handleSignOut = () => {
    signOut();
    navigate('/');
  };

  // Check if current user is the leader - either by matching the leader object or by role
  const isLeader = (currentUser && leader && currentUser.id === leader.id) || 
                  (currentUser && currentUser.role === 'LEADER');

  return (
    <ChatWindow>
      <ChatHeader>
        <ChatTitle>Dream AIM Chat Room</ChatTitle>
        <HeaderButtons>
          <HeaderButton onClick={handleSignOut}>Sign Out</HeaderButton>
        </HeaderButtons>
      </ChatHeader>

      <ChatContent>
        <MainChat>
          <ChatMessages>
            {loading ? (
              <StatusMessage>Loading messages...</StatusMessage>
            ) : messages.length === 0 ? (
              <StatusMessage>No messages yet. Start the conversation!</StatusMessage>
            ) : (
              messages.map((msg, index) => (
                <ChatMessage 
                  key={msg.id || index}
                  message={msg}
                  isCurrentUser={currentUser && msg.user_id === currentUser.id}
                />
              ))
            )}
            <div ref={messagesEndRef} />
          </ChatMessages>

          <ChatInputArea>
            <ChatInputForm onSubmit={handleSendMessage}>
              <ChatInput
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your message..."
                disabled={!isConnected}
              />
              <SendButton type="submit" disabled={!isConnected || !message.trim()}>
                Send
              </SendButton>
            </ChatInputForm>
          </ChatInputArea>
        </MainChat>

        <Sidebar>
          <SidebarHeader>
            Users Online ({users.length})
            {isLeader && (
              <StartRoundButton 
                onClick={handleStartRound}
                disabled={users.length < 1 || activeRound !== null}
              >
                Start Round
              </StartRoundButton>
            )}
          </SidebarHeader>

          <UserList users={users} currentUser={currentUser} leader={leader} />

          {!isConnected && (
            <StatusMessage isError>
              Disconnected. Trying to reconnect...
            </StatusMessage>
          )}

          {error && (
            <StatusMessage isError>
              {error}
            </StatusMessage>
          )}
        </Sidebar>
      </ChatContent>
    </ChatWindow>
  );
};

export default ChatRoom;
