import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const Game = ({ user, onLogout }) => {
  const { gameId } = useParams();
  const navigate = useNavigate();

  const [gameState, setGameState] = useState(null);
  const [boys, setBoys] = useState([]);
  const [selectedBoy, setSelectedBoy] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [guessMode, setGuessMode] = useState(false);
  const [hasGuessed, setHasGuessed] = useState(false);

  const chatContainerRef = useRef(null);
  const ws = useRef(null);

  // Initialize WebSocket connection
  useEffect(() => {
    let reconnectInterval;
    let heartbeatInterval;
    let isUnmounted = false;

    const connectWebSocket = () => {
      // Create WebSocket connection
      ws.current = new WebSocket(`ws://${window.location.hostname}:8000/api/games/ws/${user.id}`);

      ws.current.onopen = () => {
        // Clear any reconnect interval if connection is successful
        if (reconnectInterval) {
          clearInterval(reconnectInterval);
          reconnectInterval = null;
        }

        // Set up heartbeat to keep connection alive
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval);
        }

        heartbeatInterval = setInterval(() => {
          if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            console.log('Sending heartbeat ping');
            // Send a simple ping message to keep the connection alive
            // The server doesn't need to respond to this
            ws.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000); // Send heartbeat every 30 seconds
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received WebSocket message:', data);

        // Handle different message types
        switch (data.type) {
          case 'chat_message':
            // Store all messages regardless of which boy they're from
            // We'll filter them when displaying based on the selected boy
            setChatMessages(prev => {
              // Check if this message is already in the list to avoid duplicates
              const isDuplicate = prev.some(msg => msg.id === data.data.id);
              if (isDuplicate) {
                return prev;
              }

              return [...prev, {
                id: data.data.id,
                user: data.data.user,
                boy: data.data.boy,
                message: data.data.message,
                isFromUser: data.data.is_from_user,
                createdAt: data.data.created_at
              }];
            });
            break;
          case 'guess_made':
            // Update game state when someone makes a guess
            fetchGameState();
            break;
          case 'game_ended':
            // Handle game end
            fetchGameState();
            break;
          case 'pong':
            // Heartbeat response from server, no action needed
            console.log('Received heartbeat pong');
            break;
          default:
            console.log('Unknown message type:', data.type);
        }
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket connection closed', event);

        // Clear heartbeat interval
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval);
          heartbeatInterval = null;
        }

        // Only attempt to reconnect if the component is still mounted
        if (!isUnmounted) {
          // Try to reconnect every 3 seconds
          if (!reconnectInterval) {
            console.log('Setting up reconnect interval');
            reconnectInterval = setInterval(() => {
              console.log('Attempting to reconnect WebSocket');
              connectWebSocket();
            }, 3000);
          }
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    // Initial connection
    connectWebSocket();

    // Clean up WebSocket and intervals on unmount
    return () => {
      isUnmounted = true;
      if (reconnectInterval) {
        clearInterval(reconnectInterval);
      }
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
      }
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.close();
      }
    };
  }, [user.id]);

  // Fetch game state and boys on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);

        // Fetch game state
        const gameResponse = await axios.get(`/api/games/${gameId}/state`);
        setGameState(gameResponse.data);

        // Check if user has already guessed
        const userGuess = gameResponse.data.guesses.find(guess => guess.user_id === user.id);
        setHasGuessed(!!userGuess);

        // Fetch boys
        const boysResponse = await axios.get('/api/games/boys');
        setBoys(boysResponse.data);

        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching game data:', error);
        setError('Failed to load game data. Please try again.');
        setIsLoading(false);
      }
    };

    fetchData();

    // Set up interval to refresh game state
    const intervalId = setInterval(() => {
      fetchGameState();
    }, 5000);

    // Clean up interval on unmount
    return () => clearInterval(intervalId);
  }, [gameId, user.id]);

  // Fetch game state
  const fetchGameState = async () => {
    try {
      const response = await axios.get(`/api/games/${gameId}/state`);
      setGameState(response.data);

      // Check if user has already guessed
      const userGuess = response.data.guesses.find(guess => guess.user_id === user.id);
      setHasGuessed(!!userGuess);

      // If game is no longer active, redirect to waiting room after a delay
      if (!response.data.is_active) {
        setTimeout(() => {
          navigate('/waiting-room');
        }, 5000);
      }
    } catch (error) {
      console.error('Error fetching game state:', error);
    }
  };

  // Fetch chat history when a boy is selected
  useEffect(() => {
    if (selectedBoy) {
      const fetchChatHistory = async () => {
        try {
          const response = await axios.get(`/api/chat/history/${gameId}/${user.id}/${selectedBoy.id}`);
          setChatMessages(response.data.map(msg => ({
            id: msg.id,
            user: { id: msg.user_id, username: user.username },
            boy: { id: msg.boy_id, name: selectedBoy.name },
            message: msg.message,
            isFromUser: msg.is_from_user,
            createdAt: msg.created_at
          })));
        } catch (error) {
          console.error('Error fetching chat history:', error);
          setChatMessages([]);
        }
      };

      fetchChatHistory();
    } else {
      setChatMessages([]);
    }
  }, [selectedBoy, gameId, user.id, user.username]);

  // Scroll to bottom of chat when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatMessages]);

  // Handle sending a message
  const handleSendMessage = async () => {
    if (!messageInput.trim() || !selectedBoy) return;

    try {
      // Add user message to chat
      const newUserMessage = {
        id: Date.now(),
        user: { id: user.id, username: user.username },
        boy: { id: selectedBoy.id, name: selectedBoy.name },
        message: messageInput,
        isFromUser: true,
        createdAt: new Date().toISOString()
      };

      setChatMessages(prev => [...prev, newUserMessage]);
      setMessageInput('');

      // Send message to server
      await axios.post('/api/chat/', {
        message: messageInput,
        boy_id: selectedBoy.id,
        game_id: parseInt(gameId)
      }, {
        params: { user_id: user.id }
      });

      // Response will come through WebSocket
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
    }
  };

  // Handle making a guess
  const handleMakeGuess = async (boyId) => {
    try {
      await axios.post(`/api/games/${gameId}/guess`, null, {
        params: { 
          user_id: user.id,
          boy_id: boyId
        }
      });

      setHasGuessed(true);
      setGuessMode(false);
      fetchGameState();
    } catch (error) {
      console.error('Error making guess:', error);
      setError('Failed to make guess. Please try again.');
    }
  };

  // Handle next round button
  const handleNextRound = () => {
    navigate('/waiting-room');
  };

  // Handle logout
  const handleLogout = () => {
    onLogout();
  };

  // Render loading state
  if (isLoading) {
    return (
      <div className="game aim-window">
        <div className="aim-header">
          <div>Dream AIM - Loading...</div>
          <div className="aim-header-buttons">
            <div className="aim-header-button aim-minimize"></div>
            <div className="aim-header-button aim-maximize"></div>
            <div className="aim-header-button aim-close"></div>
          </div>
        </div>
        <div className="aim-content">
          <div>Loading game data...</div>
        </div>
      </div>
    );
  }

  // Render game over state
  if (gameState && !gameState.is_active) {
    return (
      <div className="game aim-window">
        <div className="aim-header">
          <div>Dream AIM - Game Over</div>
          <div className="aim-header-buttons">
            <div className="aim-header-button aim-minimize"></div>
            <div className="aim-header-button aim-maximize"></div>
            <div className="aim-header-button aim-close"></div>
          </div>
        </div>
        <div className="aim-content">
          <h2>Game Over!</h2>
          {gameState.winner_id ? (
            <p>
              {gameState.winner_id === user.id 
                ? "Congratulations! You guessed correctly!" 
                : `${gameState.users.find(u => u.id === gameState.winner_id)?.username || 'Someone'} guessed correctly!`}
            </p>
          ) : (
            <p>No one guessed correctly.</p>
          )}
          <p>
            The secret admirer was: {boys.find(boy => boy.id === gameState.secret_admirer_id)?.name || 'Unknown'}
          </p>
          <button onClick={handleNextRound}>Next Round</button>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </div>
    );
  }

  return (
    <div className="game-container">
      {/* Buddy List */}
      <div className="buddy-list aim-window">
        <div className="aim-header">
          <div>Dream AIM - Buddy List</div>
          <div className="aim-header-buttons">
            <div className="aim-header-button aim-minimize"></div>
            <div className="aim-header-button aim-maximize"></div>
            <div className="aim-header-button aim-close"></div>
          </div>
        </div>
        <div className="aim-content">
          <div className="buddy-list-header">Boys</div>
          {boys.map(boy => (
            <div 
              key={boy.id} 
              className="buddy-item"
              onClick={() => {
                if (guessMode) {
                  handleMakeGuess(boy.id);
                } else {
                  setSelectedBoy(boy);
                }
              }}
            >
              <div className="buddy-icon"></div>
              <div>{boy.name}</div>
              {guessMode && <div style={{ marginLeft: 'auto' }}>Guess</div>}
            </div>
          ))}
          <div className="game-controls">
            <button 
              onClick={() => setGuessMode(!guessMode)}
              disabled={hasGuessed}
            >
              {guessMode ? 'Cancel Guess' : 'Make a Guess'}
            </button>
            {hasGuessed && <div>You've already made your guess!</div>}
            <button onClick={handleLogout}>Logout</button>
          </div>
          {error && <div className="error-message">{error}</div>}
        </div>
      </div>

      {/* Chat Window */}
      {selectedBoy && !guessMode && (
        <div className="chat-window aim-window">
          <div className="aim-header">
            <div>Chat with {selectedBoy.name}</div>
            <div className="aim-header-buttons">
              <div className="aim-header-button aim-minimize"></div>
              <div className="aim-header-button aim-maximize"></div>
              <div className="aim-header-button aim-close" onClick={() => setSelectedBoy(null)}></div>
            </div>
          </div>
          <div className="aim-content">
            <div className="chat-messages" ref={chatContainerRef}>
              {/* Filter messages to only show those for the currently selected boy */}
              {(() => {
                const filteredMessages = chatMessages.filter(msg => msg.boy.id === selectedBoy.id);
                return filteredMessages.length === 0 ? (
                  <div>Start chatting with {selectedBoy.name}!</div>
                ) : (
                  filteredMessages.map(msg => (
                    <div key={msg.id} className="message">
                      <div className={msg.isFromUser ? "message-user" : "message-boy"}>
                        {msg.isFromUser ? user.username : selectedBoy.name}:
                      </div>
                      <div className="message-content">{msg.message}</div>
                    </div>
                  ))
                );
              })()}
            </div>
            <div className="chat-input">
              <textarea
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                placeholder={`Type a message to ${selectedBoy.name}...`}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
              <button onClick={handleSendMessage}>Send</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Game;
