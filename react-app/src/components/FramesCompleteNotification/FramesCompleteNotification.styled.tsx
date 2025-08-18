import styled, { keyframes } from 'styled-components';

const slideUp = keyframes`
  0% {
    opacity: 0;
    transform: translateY(60px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
`;

export const NotificationContainer = styled.div`
  position: fixed;
  bottom: 32px;
  right: 32px;
  background: rgb(244, 244, 244);
  color: #222;
  padding: 0;
  border-radius: 4px;
  min-width: 420px;
  min-height: 64px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.18);
  z-index: 99999;
  display: flex;
  flex-direction: row;
  align-items: stretch;
  overflow: hidden;
  opacity: 0;
  animation: ${slideUp} 0.45s cubic-bezier(0.23, 1, 0.32, 1) forwards;
`;

export const IconColumn = styled.div`
  background: #1ca14e;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  min-width: 64px;
  height: 100%;
  padding: 20px;
  margins: 1px 1px 1px 1px;
`;

export const IconWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #1ca14e;
  border-radius: 8px;
`;

export const ContentColumn = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 16px 24px 16px 20px;
  flex: 1;
  position: relative;
`;

export const NotificationTitle = styled.div`
  font-weight: 800;
  font-size: 1.15rem;
  margin-bottom: 6px;
  color: rgb(0, 0, 0);
`;

export const NotificationDivider = styled.div`
  width: 100%;
  border-bottom: 2px solid #0a3d1a;
  opacity: 0.5;
  margin-bottom: 12px;
`;

export const CloseNotificationButton = styled.button`
  position: absolute;
  top: 10px;
  right: 10px;
  background: transparent;
  border: none;
  color: #888;
  font-size: 1.4rem;
  cursor: pointer;
  z-index: 2;
  padding: 0 4px;
  line-height: 1;
  transition: color 0.15s;
  &:hover {
    color: #1ca14e;
  }
`;
