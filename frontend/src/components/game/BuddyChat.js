import React, { useState, useContext, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { AuthContext } from '../../context/AuthContext';
import { ChatContext } from '../../context/ChatContext';
import { GameContext } from '../../context/GameContext';
import { FaArrowLeft, FaPaperPlane } from 'react-icons/fa';

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
  display: flex;
  align-items: center;
  gap: 10px;
`;

const BackButton = styled.button`
  background: none;
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 0;
  margin-right: 10px;
`;

const ChatContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const MessagesContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 15px;
  background-color: var(--chat-bg);
  display: flex;
  flex-direction: column;
`;

const MessageBubble = styled.div`
  max-width: 80%;
  padding: 10px 15px;
  border-radius: 18px;
  margin-bottom: 10px;
  align-self: ${props => props.isUser ? 'flex-end' : 'flex-start'};
  background-color: ${props => props.isUser ? 'var(--primary-color)' : '#e0e0e0'};
  color: ${props => props.isUser ? 'white' : 'black'};
  position: relative;
  
  &:after {
    content: '';
    position: absolute;
    bottom: 0;
    ${props => props.isUser ? 'right: -10px;' : 'left: -10px;'}
    width: 0;
    height: 0;
    border: 10px solid transparent;
    border-top-color: ${props => props.isUser ? 'var(--primary-color)' : '#e0e0e0'};
    border-bottom: 0;
    margin-bottom: -10px;
  }
`;

const MessageTime = styled.div`
  font-size: 12px;
  color: ${props => props.isUser ? 'rgba(255, 255, 255, 0.7)' : '#888'};
  text-align: right;
  margin-top: 5px;
`;

const InputArea = styled.div`
  padding: 15px;
  border-top: 1px solid var(--window-border);
  background-color: var(--window-bg);
`;

const InputForm = styled.form`
  display: flex;
  gap: 10px;
`;

const MessageInput = styled.input`
  flex: 1;
  background-color: var(--input-bg);
  border: 2px inset var(--input-border);
  color: var(--input-text);
  padding: 10px 15px;
  font-family: 'VT323', monospace;
  font-size: 16px;
  border-radius: 20px;
`;

const SendButton = styled.button`
  background-color: var(--primary-color);
  color: white;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  
  &:hover {
    background-color: #0055aa;
  }
  
  &:active {
    transform: scale(0.95);
  }
  
  &:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
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

const BuddyInfo = styled.div`
  padding: 15px;
  background-color: #f5f5f5;
  border-bottom: 1px solid var(--window-border);
`;

const BuddyName = styled.h3`
  margin: 0 0 5px 0;
  color: var(--primary-color);
`;

const BuddyDetails = styled.p`
  margin: 0;
  font-size: 14px;
  color: #666;
`;

const BuddyChat = () => {
  const { buddyId } = useParams();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const [message, setMessage] = useState('');
  
  const { currentUser, isAuthenticated } = useContext(AuthContext);
  const { activeRound } = useContext(ChatContext);
  const { 
    buddies,
    conversations,
    currentConversation,
    conversationMessages,
    loading,
    error,
    startConversation,
    fetchConversationMessages,
    sendMessageToBuddy,
    setCurrentConversation
  } = useContext(GameContext);

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

  // Start or fetch conversation when component mounts
  useEffect(() => {
    const initConversation = async () => {
      if (isAuthenticated && currentUser && buddyId) {
        // Check if conversation already exists
        const existingConv = conversations.find(
          conv => conv.buddy_id === parseInt(buddyId) && conv.round_id === activeRound?.id
        );
        
        if (existingConv) {
          setCurrentConversation(existingConv);
          await fetchConversationMessages(existingConv.id);
        } else {
          const newConv = await startConversation(parseInt(buddyId));
          if (newConv) {
            await fetchConversationMessages(newConv.id);
          }
        }
      }
    };
    
    initConversation();
  }, [isAuthenticated, currentUser, buddyId, activeRound]);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversationMessages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (message.trim() && currentConversation) {
      await sendMessageToBuddy(currentConversation.id, message);
      setMessage('');
    }
  };

  const handleBackToGame = () => {
    setCurrentConversation(null);
    navigate('/game');
  };

  // Find the buddy
  const buddy = buddies.find(b => b.id === parseInt(buddyId));

  return (
    <ChatWindow>
      <ChatHeader>
        <ChatTitle>
          <BackButton onClick={handleBackToGame}>
            <FaArrowLeft />
          </BackButton>
          Chat with {buddy?.name || 'Buddy'}
        </ChatTitle>
      </ChatHeader>
      
      {buddy && (
        <BuddyInfo>
          <BuddyName>{buddy.name}</BuddyName>
          <BuddyDetails>
            {buddy.gender}, {buddy.sexual_orientation}, {buddy.gender_identity}
          </BuddyDetails>
        </BuddyInfo>
      )}
      
      <ChatContent>
        <MessagesContainer>
          {loading ? (
            <LoadingMessage>Loading conversation...</LoadingMessage>
          ) : error ? (
            <ErrorMessage>{error}</ErrorMessage>
          ) : conversationMessages.length === 0 ? (
            <LoadingMessage>Start chatting with {buddy?.name || 'your buddy'}!</LoadingMessage>
          ) : (
            conversationMessages.map((msg, index) => (
              <MessageBubble 
                key={msg.id || index} 
                isUser={msg.sender_type === 'user'}
              >
                {msg.content}
                <MessageTime isUser={msg.sender_type === 'user'}>
                  {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                </MessageTime>
              </MessageBubble>
            ))
          )}
          <div ref={messagesEndRef} />
        </MessagesContainer>
        
        <InputArea>
          <InputForm onSubmit={handleSendMessage}>
            <MessageInput
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your message..."
              disabled={loading || !currentConversation}
            />
            <SendButton 
              type="submit" 
              disabled={loading || !message.trim() || !currentConversation}
            >
              <FaPaperPlane />
            </SendButton>
          </InputForm>
        </InputArea>
      </ChatContent>
    </ChatWindow>
  );
};

export default BuddyChat;