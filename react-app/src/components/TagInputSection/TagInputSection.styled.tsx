import styled from 'styled-components';

export const TagListStyled = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
  max-width: 420px; /* or another fixed value, matching modal content or your design */
  width: 100%;
  box-sizing: border-box;
`;

export const TagItemStyled = styled.span`
  background: #e0e0e0;
  color: #333;
  border-radius: 10px;
  padding: 2px 8px;
  font-size: 0.85rem;
  cursor: pointer;
  opacity: 0.95;
  margin-bottom: 0;
  /* No width or flex-basis, so it only fits content */
`;

export const TagRemoveIcon = styled.span`
  margin-left: 4px;
  color: #000;
  font-weight: 700;
`;

export const TagInputRow = styled.div`
  display: flex;
  gap: 16px;
  justify-content: flex-start;
  width: 100%;
  margin-bottom: 8px;
`;

export const TagInputBox = styled.input`
  text-align: left;
  width: 40%;
  min-width: 180px;
  max-width: 340px;
  padding: 10px 14px;
  font-size: 1rem;
  border: 2px solid #d3d3d3;
  border-radius: 4px;
`;

export const QuickSelectTagsStyled = styled.div`
  justify-content: flex-start;
  width: 100%;
  display: flex;
  flex-direction: column;
  margin-top: 16px;
  gap: 8px;
`;

export const QuickSelectRow = styled.div`
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
`;

export const TagInputSectionContainer = styled.div`
  display: flex;
  flex-direction: row;
  width: 100%;
  align-items: flex-start;
  margin-top: 8px;
`;

export const ButtonRowBelowInput = styled.div`
  display: flex;
  flex-direction: row;
  gap: 8px;
  margin-top: 8px;
`;

export const QuickTagButton = styled.button`
  background: #f7f7f7;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 4px 10px;
  font-size: 0.95rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-family: inherit;
  font-weight: 500;
  transition: background 0.15s;
  &:hover {
    background: #e0e0e0;
  }
  &.prev-annotation-match {
    background: #43e97b;
    color: white;
    border-color: #43e97b;
  }
  &.prev-annotation-match:hover {
    background:rgb(40, 199, 93);
    border-color:rgb(40, 199, 93);
  }
`;

export const TagActionButtonsRow = styled.div`
  display: flex;
  gap: 8px;
  margin-top: 4px;
`;
