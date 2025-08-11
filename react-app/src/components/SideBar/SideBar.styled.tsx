import styled from 'styled-components';

// Styled components for SideBar
export const Aside = styled.aside`
  width: 20vw;
  min-width: 180px;
  max-width: 400px;
  background: #f8f9fa;
  height: 100vh;
  padding: 88px 12px 24px 12px;
  box-sizing: border-box;
  border-right: 3px solid rgb(229, 229, 229);
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const MenuTitle = styled.h2`
  font-size: 1.1rem;
  margin-top: 3rem;
  margin-bottom: 1rem;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const MenuList = styled.ul`
  list-style: none;
  padding: 0;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const AnnotationContainer = styled.div<{ isCNN?: boolean }>`
  margin-bottom: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 120px;
  border-left: 6px solid ${props => props.isCNN ? 'rgba(40,167,69,0.5)' : 'rgba(0,123,255,0.5)'};
  background: ${props => props.isCNN ? 'rgba(40,167,69,0.1)' : 'rgba(0,123,255,0.1)'};
  padding-left: 16px;
  justify-content: center;
  height: 120px;
  padding-top: 6px;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const TagPillContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const TagPill = styled.span`
  background: #e0e0e0;
  color: #333;
  border-radius: 12px;
  padding: 4px 10px;
  font-size: 0.95rem;
  margin-bottom: 4px;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const ActionList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;