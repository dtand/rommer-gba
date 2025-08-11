import React from 'react';
import styled, { keyframes } from 'styled-components';

const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(255, 255, 255, 0.5);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const Content = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18px;
`;

const LoadingText = styled.div`
  font-size: 2rem;
  color: #333;
  font-weight: 600;
`;

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const Spinner = styled.div`
  border: 6px solid #e0e0e0;
  border-top: 6px solid #007bff;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  animation: ${spin} 1s linear infinite;
`;

const LoadingOverlay: React.FC = () => (
  <Overlay>
    <Content>
      <LoadingText>Loading</LoadingText>
      <Spinner />
    </Content>
  </Overlay>
);

export default LoadingOverlay;
