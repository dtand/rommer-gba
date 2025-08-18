import styled from 'styled-components';

export const FramePreviewSectionContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;

export const FramePreviewButtonsRow = styled.div`
  margin-top: 16px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
`;

export const FramePreviewNoButtons = styled.span`
  color: #aaa;
  font-size: 0.85rem;
`;

export const TagList = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
  justify-content: flex-start;
  align-items: flex-start;
`;

export const TagItem = styled.span`
  background: #e0e0e0;
  color: #333;
  border-radius: 10px;
  padding: 2px 7px;
  font-size: 0.82rem;
`;
