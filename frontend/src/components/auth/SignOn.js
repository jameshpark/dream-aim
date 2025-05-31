import React, { useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { AuthContext } from '../../context/AuthContext';

const SignOnWindow = styled.div`
  background-color: var(--window-bg);
  border: 2px solid var(--window-border);
  border-radius: 5px;
  box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 400px;
  padding: 20px;
  margin: 0 auto;
`;

const SignOnHeader = styled.div`
  text-align: center;
  margin-bottom: 20px;
`;

const Logo = styled.h1`
  font-size: 32px;
  color: var(--primary-color);
  margin-bottom: 5px;
`;

const Tagline = styled.p`
  font-size: 14px;
  color: var(--text-color);
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 5px;
`;

const Label = styled.label`
  font-size: 16px;
  font-weight: bold;
`;

const Input = styled.input`
  background-color: var(--input-bg);
  border: 2px inset var(--input-border);
  color: var(--input-text);
  padding: 8px 10px;
  font-family: 'VT323', monospace;
  font-size: 16px;
`;

const ButtonGroup = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
`;

const Button = styled.button`
  background-color: var(--button-bg);
  border: 2px outset var(--button-border);
  color: var(--button-text);
  padding: 8px 15px;
  font-family: 'VT323', monospace;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.1s;

  &:hover {
    background-color: #e0e0e0;
  }

  &:active {
    border-style: inset;
    transform: translateY(1px);
  }
`;

const ErrorMessage = styled.div`
  color: var(--error-color);
  margin-top: 10px;
  text-align: center;
`;

const SignOn = () => {
  const [screenName, setScreenName] = useState('');
  const [password, setPassword] = useState('');
  const { signIn, isAuthenticated, loading, error } = useContext(AuthContext);
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/chat');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!screenName || !password) {
      return;
    }

    const success = await signIn(screenName, password);

    if (success) {
      navigate('/chat');
    }
  };

  return (
    <SignOnWindow>
      <SignOnHeader>
        <Logo>Dream AIM</Logo>
        <Tagline>America Online Instant Messenger</Tagline>
      </SignOnHeader>

      <Form onSubmit={handleSubmit}>
        <FormGroup>
          <Label htmlFor="screenName">Screen Name:</Label>
          <Input
            type="text"
            id="screenName"
            value={screenName}
            onChange={(e) => setScreenName(e.target.value)}
            required
          />
        </FormGroup>

        <FormGroup>
          <Label htmlFor="password">Passphrase:</Label>
          <Input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter the passphrase"
            required
          />
        </FormGroup>

        {error && <ErrorMessage>{error}</ErrorMessage>}

        <ButtonGroup>
          <Button type="submit" disabled={loading} style={{ margin: '0 auto' }}>
            {loading ? 'Loading...' : 'Sign On'}
          </Button>
        </ButtonGroup>
      </Form>
    </SignOnWindow>
  );
};

export default SignOn;
