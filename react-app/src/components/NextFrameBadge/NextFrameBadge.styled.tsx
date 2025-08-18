import styled, { keyframes } from 'styled-components';

export const pulse = keyframes`
  0% { box-shadow: 0 0 0 0 rgba(98, 0, 234, 0.5), 0 0 0 0 rgba(0, 180, 255, 0.5); }
  50% { box-shadow: 0 0 0 10px rgba(0, 180, 255, 0), 0 0 0 20px rgba(98, 0, 234, 0); }
  100% { box-shadow: 0 0 0 0 rgba(98, 0, 234, 0.5), 0 0 0 0 rgba(0, 180, 255, 0.5); }
`;

export const Badge = styled.div`
  position: absolute;
  top: -10px;
  left: -10px;
  background: linear-gradient(90deg, #00b4ff 0%, #6200ea 100%);
  color: #fff;
  font-weight: bold;
  font-size: 0.92rem;
  padding: 3px 14px;
  border-radius: 16px;
  z-index: 9999;
  box-shadow: 0 2px 12px rgba(98,0,234,0.18);
  animation: ${pulse} 1.5s infinite;
  letter-spacing: 0.01em;
  pointer-events: none;
  border: 2px solid #fff;
  text-shadow: 0 1px 4px rgba(98,0,234,0.18);
`;
