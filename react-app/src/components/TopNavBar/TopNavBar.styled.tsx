import styled from 'styled-components';

// Styled components for TopNavBar

export const NavBar = styled.nav`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background: linear-gradient(90deg, #fff 0%, #eaeaea 100%);
  color: #222;
  padding: 0 24px;
  min-height: 105px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  z-index: 100;
  box-shadow: 0 2px 8px #0005;
  box-sizing: border-box;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
  @media (max-width: 600px) {
    padding: 0 8px;
    min-height: 140px;
  }
`;

export const Row = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  width: 100%;
  margin-top: 8px;
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
  border: 2px solidrgb(225, 225, 225);
  font-size: 1rem;
  min-width: 100px;
  background:rgb(237, 237, 237);
  color: #222;
  box-shadow: 0 2px 8px #007bff22;
  font-weight: 500;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const Button = styled.button`
  background: #007bff;
  color: #fff;
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
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
  &:hover {
    background: #0056b3;
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

export const SecondRow = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  margin-top: 8px;
`;

export const GameName = styled.span`
  font-size: 1.1rem;
  font-weight: 800;
  color: #222;
  margin-right: 18px;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const Pill = styled.span<{ color?: string }>`
  display: inline-block;
  font-size: 0.95em;
  font-weight: 500;
  background: ${({ color }) => color || '#e0e0e0'};
  color: #fff;
  border-radius: 12px;
  padding: 4px 14px;
  margin-right: 10px;
`;

export const ProgressText = styled.span`
  font-size: 0.95em;
  color: #333;
  margin-right: 18px;
`;

export const ProgressBarContainer = styled.div`
  flex: 1;
  height: 16px;
  background: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
  width: 100%;
`;

export const ProgressBarFill = styled.div<{ percent: number }>`
  height: 100%;
  width: ${({ percent }) => percent}%;
  background: linear-gradient(90deg, #4caf50 0%, #43e97b 100%);
  border-radius: 10px;
  transition: width 0.3s;
`;

export const MemoryButton = styled(Button)`
  background: linear-gradient(90deg, #00bcd4 0%, #8e24aa 100%);
  color: #fff;
  border: 2px solid #8e24aa;
  box-shadow: 0 0 12px #8e24aa55, 0 2px 8px #00bcd455;
  border-radius: 24px;
  font-weight: 700;
  position: relative;
  transition: box-shadow 0.2s, transform 0.2s;
  max-width: 180px;
  min-width: 160px;
  padding: 10px 24px;
  overflow: visible;
  &:hover {
    box-shadow: 0 0 24px #8e24aa99, 0 4px 16px #00bcd499;
    transform: scale(1.05);
    background: linear-gradient(90deg, #8e24aa 0%, #00bcd4 100%);
  }
  /* Move badge to top right, pulled down a bit */
  &::after {
    content: 'Analyzer';
    position: absolute;
    top: -10px;
    left: 18px;
    background: #fff;
    color: #8e24aa;
    font-size: 0.75em;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 8px;
    box-shadow: 0 2px 8px #8e24aa22;
    letter-spacing: 0.5px;
    opacity: 0.85;
    pointer-events: none;
  }
  svg {
    animation: memoryPulse 1.2s infinite alternate;
  }
  @keyframes memoryPulse {
    0% { filter: drop-shadow(0 0 0 #8e24aa); }
    100% { filter: drop-shadow(0 0 8px #8e24aa); }
  }
`;

export const LogoImage = styled.img`
  height: 32px;
  width: 128px;
  margin-top: 2px;
  object-fit: contain;
`;
