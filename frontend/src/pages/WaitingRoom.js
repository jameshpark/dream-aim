import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const WaitingRoom = ({ user, onLogout }) => {
  const [users, setUsers] = useState([]);
  const [leaderId, setLeaderId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [gameInProgress, setGameInProgress] = useState(false);
  const navigate = useNavigate();

  // Join waiting room on component mount
  useEffect(() => {
    const joinWaitingRoom = async () => {
      try {
        setIsLoading(true);
        const response = await axios.post('/api/games/waiting-room/join', null, {
          params: { user_id: user.id }
        });
        setUsers(response.data.users);
        setLeaderId(response.data.leader_id);
        setGameInProgress(false);
      } catch (error) {
        console.error('Error joining waiting room:', error);
        if (error.response?.status === 400 && error.response?.data?.detail?.includes('game is already in progress')) {
          setGameInProgress(true);
        } else {
          setError('Failed to join waiting room. Please try again.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    joinWaitingRoom();

    // Leave waiting room on component unmount
    return () => {
      const leaveWaitingRoom = async () => {
        try {
          await axios.post('/api/games/waiting-room/leave', null, {
            params: { user_id: user.id }
          });
        } catch (error) {
          console.error('Error leaving waiting room:', error);
        }
      };

      leaveWaitingRoom();
    };
  }, [user.id]);

  // Start a new game (only for leader)
  const handleStartGame = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post('/api/games/start', null, {
        params: { leader_id: user.id }
      });
      navigate(`/game/${response.data.id}`);
    } catch (error) {
      console.error('Error starting game:', error);
      setError('Failed to start game. Please try again.');
      setIsLoading(false);
    }
  };

  // Handle logout
  const handleLogout = () => {
    onLogout();
  };

  // Check if current user is the leader
  const isLeader = user.id === leaderId;

  return (
    <div className="waiting-room aim-window">
      <div className="aim-header">
        <div>Dream AIM - Waiting Room</div>
        <div className="aim-header-buttons">
          <div className="aim-header-button aim-minimize"></div>
          <div className="aim-header-button aim-maximize"></div>
          <div className="aim-header-button aim-close"></div>
        </div>
      </div>
      <div className="aim-content">
        {isLoading ? (
          <div>Loading...</div>
        ) : gameInProgress ? (
          <div>
            <p>A game is currently in progress.</p>
            <p>Please wait for the current game to end before joining.</p>
          </div>
        ) : (
          <>
            <div className="waiting-room-users">
              <h3>Players in Waiting Room</h3>
              {users.length === 0 ? (
                <p>No players in waiting room</p>
              ) : (
                <ul>
                  {users.map((waitingUser) => (
                    <li key={waitingUser.id}>
                      {waitingUser.username}
                      {waitingUser.id === leaderId && (
                        <span className="leader-badge">Leader</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="waiting-room-controls">
              {isLeader ? (
                <button onClick={handleStartGame} disabled={isLoading || users.length < 1}>
                  Start Game
                </button>
              ) : (
                <p>Waiting for leader to start the game...</p>
              )}
              <button onClick={handleLogout}>Logout</button>
            </div>
            {error && <div className="error-message">{error}</div>}
          </>
        )}
      </div>
    </div>
  );
};

export default WaitingRoom;