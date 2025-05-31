import React from 'react';
import styled from 'styled-components';
import { FaCrown } from 'react-icons/fa';

const UserListContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 5px;
`;

const UserItem = styled.div`
  padding: 8px 10px;
  margin-bottom: 5px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  background-color: ${props => props.isCurrentUser ? 'var(--primary-color)' : 'transparent'};
  color: ${props => props.isCurrentUser ? 'white' : 'var(--text-color)'};
  font-weight: ${props => props.isCurrentUser ? 'bold' : 'normal'};
  
  &:hover {
    background-color: ${props => props.isCurrentUser ? 'var(--primary-color)' : '#e0e0e0'};
  }
`;

const UserIcon = styled.div`
  width: 20px;
  height: 20px;
  margin-right: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${props => props.isLeader ? 'gold' : 'inherit'};
`;

const UserName = styled.div`
  flex: 1;
`;

const UserList = ({ users, currentUser, leader }) => {
  // Sort users: leader first, then current user, then alphabetically
  const sortedUsers = [...users].sort((a, b) => {
    // Leader comes first
    if (leader && a.id === leader.id) return -1;
    if (leader && b.id === leader.id) return 1;
    
    // Current user comes next
    if (currentUser && a.id === currentUser.id) return -1;
    if (currentUser && b.id === currentUser.id) return 1;
    
    // Then alphabetically by screen name
    return a.screen_name.localeCompare(b.screen_name);
  });

  return (
    <UserListContainer>
      {sortedUsers.length === 0 ? (
        <div style={{ padding: '10px', fontStyle: 'italic', textAlign: 'center' }}>
          No users online
        </div>
      ) : (
        sortedUsers.map(user => (
          <UserItem 
            key={user.id} 
            isCurrentUser={currentUser && user.id === currentUser.id}
          >
            <UserIcon isLeader={leader && user.id === leader.id}>
              {leader && user.id === leader.id ? <FaCrown /> : '•'}
            </UserIcon>
            <UserName>
              {user.screen_name}
              {currentUser && user.id === currentUser.id ? ' (You)' : ''}
            </UserName>
          </UserItem>
        ))
      )}
    </UserListContainer>
  );
};

export default UserList;