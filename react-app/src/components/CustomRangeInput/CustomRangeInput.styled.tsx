import styled from 'styled-components';

export const RangeInputContainer = styled.div`
  position: absolute;
  left: 50%;
  top: 100%;
  transform: translateX(-50%);
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 16px;
  z-index: 9999;
  min-width: 260px;
  margin-top: 4px;
  box-shadow: 0 2px 12px #eaeaea;
`;

export const RangeInputGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
  margin-bottom: 12px;
  align-items: center;
`;

export const RangeLabel = styled.label`
  text-align: right;
  font-weight: 500;
`;

export const RangeInput = styled.input`
  width: 100px;
`;

export const RangeButtonRow = styled.div`
  text-align: center;
`;

export const RangeButton = styled.button`
  margin-right: 8px;
`;
