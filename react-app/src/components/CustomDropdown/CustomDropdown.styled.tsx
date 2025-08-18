import styled from 'styled-components';

export const DropdownWrapper = styled.div<{ width?: string }>`
  position: relative;
  width: ${({ width }) => width || '100%'};
`;

export const DropdownButton = styled.button<{ width?: string }>`
  width: ${({ width }) => width || '100%'};
  padding: 8px 12px;
  background: #fff;
  color: #222;
  border: 2px solid #d3d3d3;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  box-shadow: 0 2px 8px #eaeaea;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const DropdownList = styled.ul<{ width?: string }>`
  position: absolute;
  top: 110%;
  left: 0;
  width: ${({ width }) => width || '100%'};
  background: #fff;
  border: 2px solid #d3d3d3;
  border-radius: 4px;
  box-shadow: 0 4px 16px #eaeaea;
  margin: 0;
  padding: 0;
  z-index: 1000;
  list-style: none;
  max-height: 320px;
  overflow-y: auto;
`;

export const DropdownHeader = styled.li`
  font-weight: 600;
  color: #888;
  background: #f5f5f5;
  padding: 10px 12px;
  border-bottom: 1px solid #e0e0e0;
`;

export const DropdownItem = styled.li`
  padding: 10px 12px;
  color: #222;
  cursor: pointer;
  background: #fff;
  &:hover {
    background: #f5f5f5;
  }
`;

export const DropdownCaret = styled.span`
  margin-left: 8px;
  font-size: 1.2em;
  color: #888;
`;
