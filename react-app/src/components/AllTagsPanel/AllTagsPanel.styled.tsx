import styled, { keyframes } from 'styled-components';

export const slideIn = keyframes`
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
`;

export const AllTagsContainer = styled.div`
  position: fixed;
  top: 0;
  right: 0;
  height: 100vh;
  width: 300px;
  background: #fff;
  box-shadow: -4px 0 16px rgba(0,0,0,0.12);
  z-index: 2000;
  display: flex;
  flex-direction: column;
  animation: ${slideIn} 0.35s cubic-bezier(0.4, 0, 0.2, 1);
`;

export const AllTagsHeader = styled.div`
  padding: 18px 24px 10px 24px;
  font-weight: bold;
  font-size: 1.2rem;
  border-bottom: 1px solid #e0e0e0;
`;

export const AllTagsList = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 18px 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

export const TagButton = styled.button`
  background: #e8f5e9;
  color: #388e3c;
  border: none;
  border-radius: 18px;
  padding: 8px 18px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.15s;
  &:hover {
    background: #c8e6c9;
  }
`;

export const CloseButton = styled.button`
  position: absolute;
  top: 12px;
  right: 18px;
  background: transparent;
  border: none;
  font-size: 1.5rem;
  color: #888;
  cursor: pointer;
  z-index: 10;
`;

export const SearchBar = styled.input`
  margin: 16px 24px 0 24px;
  padding: 8px 14px;
  border: 1.5px solid #d3d3d3;
  border-radius: 6px;
  font-size: 1rem;
  outline: none;
  width: calc(100% - 48px);
  box-sizing: border-box;
`;

export const TagRow = styled.div`
  display: flex;
  align-items: center;
  padding: 8px 18px;
  font-size: 1rem;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  background: #fff;
  transition: background 0.15s;
  &:hover {
    background: #f5f5f5;
  }
`;
