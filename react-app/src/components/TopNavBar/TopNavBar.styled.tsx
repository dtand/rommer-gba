import styled from 'styled-components';

// Styled components for TopNavBar

export const NavBar = styled.nav`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background: #007bff;
  color: #fff;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  z-index: 100;
  box-shadow: 0 2px 8px #0002;
  box-sizing: border-box;
  @media (max-width: 600px) {
    padding: 0 8px;
    height: auto;
  }
`;

export const Logo = styled.div`
  font-weight: bold;
  font-size: 1.3rem;
  margin-right: 32px;
`;

export const Row = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  width: 100%;
  box-sizing: border-box;
  @media (max-width: 600px) {
    flex-direction: column;
    align-items: stretch;
  }
`;

export const LeftGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 20px;
  min-width: 0;
  max-width: 60%;
  @media (max-width: 600px) {
    max-width: 100%;
    flex-wrap: wrap;
    gap: 10px;
  }
`;

export const RightGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 20px;
  flex-shrink: 1;
  flex-wrap: wrap;
  min-width: 0;
  @media (max-width: 600px) {
    max-width: 100%;
    flex-wrap: wrap;
    gap: 10px;
  }
`;

export const Dropdown = styled.select`
  padding: 6px 12px;
  border-radius: 4px;
  border: none;
  font-size: 1rem;
  min-width: 120px;
`;

export const Button = styled.button`
  background: #fff;
  color: #007bff;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  &:hover {
    background: #e6f0ff;
  }
  @media (max-width: 600px) {
    max-width: 100%;
    font-size: 0.95rem;
    padding: 8px 8px;
  }
`;

export const Icon = styled.span`
  display: inline-flex;
  align-items: center;
  margin-right: 8px;
`;

export const OptionText = styled.span`
  display: inline-flex;
  align-items: center;
`;
