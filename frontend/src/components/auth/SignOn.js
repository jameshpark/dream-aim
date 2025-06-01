import React, { useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { AuthContext } from '../../context/AuthContext';
import splashImage from '../../assets/images/splash.png';
import signOnButtonImage from '../../assets/images/sign-on.png';

const SignOnWindow = styled.div`
  background-color: #B2B1B3;
  border: 2px solid #000000;
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
  box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.2);
`;

const TitleBar = styled.div`
  background-color: #170774;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 3px;
  height: 22px;
`;

const TitleText = styled.div`
  display: flex;
  align-items: center;
  font-size: 14px;
`;

const TitleIcon = styled.img`
  height: 16px;
  margin-right: 5px;
`;

const WindowControls = styled.div`
  display: flex;
`;

const WindowButton = styled.button`
  background-color: #B2B1B3;
  border: 1px outset #FFFFFF;
  width: 16px;
  height: 16px;
  margin-left: 2px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-family: 'Webdings', sans-serif;
  font-size: 10px;
  cursor: pointer;

  &:active {
    border-style: inset;
  }
`;

const SplashImage = styled.img`
  display: block;
  margin: 10px auto;
  max-width: 100%;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  padding: 10px 20px 20px;
`;

const FormTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 15px;
`;

const FormRow = styled.tr``;

const FormLabelCell = styled.td`
  text-align: left;
  padding: 5px;
  font-size: 14px;
  color: black;
`;

const FormInputCell = styled.td`
  padding: 5px;
`;

const Input = styled.input`
  background-color: white;
  border: 2px inset #808080;
  color: black;
  padding: 5px;
  width: 100%;
  font-family: 'VT323', monospace;
  font-size: 14px;
`;

const ButtonContainer = styled.div`
  display: flex;
  justify-content: flex-end;
`;

const SignOnButton = styled.button`
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;

  &:active {
    transform: translateY(1px);
  }

  img {
    display: block;
  }
`;

const ErrorMessage = styled.div`
  color: red;
  margin-top: 10px;
  text-align: center;
  font-size: 14px;
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
      <TitleBar>
        <TitleText>
          <TitleIcon src={`${process.env.PUBLIC_URL}/favicon.svg`} alt="AIM Icon" />
          Sign On
        </TitleText>
        <WindowControls>
          <WindowButton title="Minimize">0</WindowButton>
          <WindowButton title="Maximize">1</WindowButton>
          <WindowButton title="Close">r</WindowButton>
        </WindowControls>
      </TitleBar>

      <SplashImage src={splashImage} alt="AOL Instant Messenger" />

      <Form onSubmit={handleSubmit}>
        <FormTable>
          <tbody>
            <FormRow>
              <FormLabelCell>Screen Name</FormLabelCell>
              <FormInputCell>
                <Input
                  type="text"
                  id="screenName"
                  value={screenName}
                  onChange={(e) => setScreenName(e.target.value)}
                  required
                />
              </FormInputCell>
            </FormRow>
            <FormRow>
              <FormLabelCell>Passphrase</FormLabelCell>
              <FormInputCell>
                <Input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </FormInputCell>
            </FormRow>
          </tbody>
        </FormTable>

        {error && <ErrorMessage>{error}</ErrorMessage>}

        <ButtonContainer>
          <SignOnButton type="submit" disabled={loading}>
            <img src={signOnButtonImage} alt="Sign On" />
          </SignOnButton>
        </ButtonContainer>
      </Form>
    </SignOnWindow>
  );
};

export default SignOn;
