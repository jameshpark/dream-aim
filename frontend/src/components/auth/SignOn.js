import React, {useState, useContext, useEffect} from 'react';
import {useNavigate} from 'react-router-dom';
import styled from 'styled-components';
import {AuthContext} from '../../context/AuthContext';
import splashImage from '../../assets/images/splash.png';
import signOnButtonImage from '../../assets/images/sign-on-button.png';
import aimButtonsImage from '../../assets/images/help-setup-buttons.png';
import screenNameLabel from '../../assets/images/screen-name-label.png';
import passwordLabel from '../../assets/images/password-label.png';
import titleBarTitleImage from '../../assets/images/title-bar-title.png';
import titleBarButtonseImage from '../../assets/images/title-bar-buttons.png';

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
    height: clamp(10px, 5vw, 38px);
`;

const TitleText = styled.div`
    height: clamp(10px, 5vw, 35px);
    width: auto;
    
    img {
        height: clamp(10px, 5vw, 35px);
        display: block;
        object-fit: contain;
    }
`;

const WindowControls = styled.div`
    height: clamp(10px, 5vw, 35px);
    width: auto;

    img {
        height: clamp(10px, 5vw, 35px);
        display: block;
        object-fit: contain;
    }
`;

const SplashImage = styled.img`
    display: block;
    margin: 10px auto;
    max-width: 100%;
`;

const FormRow = styled.tr`
    vertical-align: center;
`;

const Input = styled.input`
    background-color: white;
    border: 2px inset #808080;
    color: black;
    padding: 5px;
    width: 100%;
    font-family: 'VT323', monospace;
    font-size: clamp(14px, 2vw, 16px);
    height: clamp(30px, 5vw, 40px);
    box-sizing: border-box;
`;

const FormTable = styled.table`
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 15px;
    max-width: 100%;
`;

const FormLabelCell = styled.td`
    width: 40%;
    padding: 0px;
    color: black;
    vertical-align: middle;

    img {
        height: clamp(30px, 5vw, 40px);
        width: auto;
        max-width: 100%;
        display: block;
        object-fit: contain;
    }
`;

const PasswordLabelCell = styled(FormLabelCell)`
    img {
        width: 75%;
        height: auto; // Allow height to adjust based on width
        max-height: clamp(30px, 5vw, 40px); // Ensure it doesn't exceed input height
    }
`;


const FormInputCell = styled.td`
    width: 60%;
    padding-top: 6px;
    vertical-align: middle;
`;

const Form = styled.form`
    display: flex;
    flex-direction: column;
    padding: clamp(5px, 2vw, 20px);
    width: 100%;
    box-sizing: border-box;
`;

const AimButtonsContainer = styled.div`
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
`;

const HelpSettingsButtonsContainer = styled.div`
    justify-self: start;
    width: 160px;
    height: 80px;
`;

const SignOnButtonContainer = styled.div`
    justify-self: end;
    width: 90px;
    height: 90px;
    padding-top: 8px;
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
        display: grid;
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
    const {signIn, isAuthenticated, loading, error} = useContext(AuthContext);
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
                    <img src={titleBarTitleImage} alt="Title Bar Title"/>
                </TitleText>
                <WindowControls>
                    <img src={titleBarButtonseImage} alt="Title Bar Buttons"/>
                </WindowControls>
            </TitleBar>

            <SplashImage src={splashImage} alt="AOL Instant Messenger"/>

            <Form onSubmit={handleSubmit}>
                <FormTable>
                    <tbody>
                    <FormRow>
                        <FormLabelCell>
                            <img src={screenNameLabel} alt="Screen Name Label"/>
                        </FormLabelCell>
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
                        <PasswordLabelCell>
                            <img src={passwordLabel} alt="Password Label"/>
                        </PasswordLabelCell>
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

                <AimButtonsContainer>
                    <HelpSettingsButtonsContainer>
                        <img src={aimButtonsImage} alt="Help Settings buttons graphic" width="100%" height="100%"/>
                    </HelpSettingsButtonsContainer>
                    <SignOnButtonContainer>
                        <SignOnButton type="submit" disabled={loading}>
                            <img src={signOnButtonImage} alt="Sign On" width="100%" height="100%"/>
                        </SignOnButton>
                    </SignOnButtonContainer>
                </AimButtonsContainer>
            </Form>
        </SignOnWindow>
    );
};

export default SignOn;
