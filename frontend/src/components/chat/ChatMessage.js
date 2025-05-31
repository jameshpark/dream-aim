import React from 'react';
import styled from 'styled-components';
import { format } from 'date-fns';

const MessageContainer = styled.div`
  margin-bottom: 10px;
  padding: 5px 0;
  border-bottom: 1px solid #eee;
`;

const MessageHeader = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
`;

const Username = styled.span`
  font-weight: bold;
  color: ${props => props.isCurrentUser ? 'var(--primary-color)' : 'var(--text-color)'};
`;

const Timestamp = styled.span`
  font-size: 12px;
  color: #888;
`;

const MessageContent = styled.div`
  word-wrap: break-word;
`;

const ChatMessage = ({ message, isCurrentUser }) => {
  // Format the timestamp
  const formattedTime = message.timestamp 
    ? format(new Date(message.timestamp), 'h:mm a')
    : '';

  return (
    <MessageContainer>
      <MessageHeader>
        <Username isCurrentUser={isCurrentUser}>
          {message.username || 'Unknown User'}
        </Username>
        <Timestamp>{formattedTime}</Timestamp>
      </MessageHeader>
      <MessageContent>
        {message.content}
      </MessageContent>
    </MessageContainer>
  );
};

export default ChatMessage;