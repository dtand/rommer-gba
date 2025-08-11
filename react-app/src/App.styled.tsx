import styled from 'styled-components';

export const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  position: fixed;
  top: 0;
  left: 0;
  overflow: hidden;
  background: linear-gradient(135deg, #222 0%, #444 100%);
`;

export const MainContent = styled.div`
  display: flex;
  flex: 1;
  height: calc(100vh - 64px); /* Adjust for TopNavBar height */
  overflow: hidden;
  background: #222;
  box-shadow: 0 2px 16px rgba(0,0,0,0.08);
`;

export const GridArea = styled.div`
  width: 80vw;
  height: 100%;
  overflow: hidden;
  display: flex;
  background: #333;
  box-shadow: 0 0 8px rgba(0,0,0,0.08);
`;
