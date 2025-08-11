import styled from 'styled-components';

export const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
`;

export const ModalContent = styled.div`
  background: #fff;
  border-radius: 12px;
  padding: 32px;
  min-width: 820px;
  max-width: 1600px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15);
  position: relative;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const CloseButton = styled.button`
  position: absolute;
  top: 16px;
  right: 16px;
  font-size: 18px;
  background: none;
  border: none;
  cursor: pointer;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const ModalTitle = styled.h2`
  margin-bottom: 24px;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const ModalPre = styled.pre`
  background: #f7f7f7;
  border-radius: 6px;
  padding: 16px;
  font-size: 1rem;
  max-height: 60vh;
  overflow-y: auto;
  font-family: 'Inter', 'Nunito', 'Segoe UI', 'Avenir', Helvetica, Arial, sans-serif;
`;

export const ModalDivider = styled.div`
  width: 100%;
  height: 1px;
  background: #e0e0e0;
  margin: 18px 0;
`;

export const ModalSection = styled.div`
  display: flex;
  flex-direction: row;
  gap: 32px;
  margin-bottom: 18px;
`;

export const ModalCol = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

export const FrameImagePreview = styled.img`
  width: 420px;
  height: 420px;
  object-fit: contain;
  border-radius: 8px;
  background: #f7f7f7;
  border: 1px solid #e0e0e0;
`;

export const ModalButtonRow = styled.div`
  display: flex;
  gap: 16px;
  justify-content: flex-start;
  margin-top: 12px;
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
  border-radius: 12px;
  padding: 4px 10px;
  font-size: 0.95rem;
`;

export const QuickSelectTags = styled.div`
  display: flex;
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
  &:hover {
    background: #e0e0e0;
  }
`;

export const ModalTagsRow = styled.div`
  width: 100%;
  margin-top: 32px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
`;

export const FrameIdPillRow = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 10px;
  max-width: 100%;
  overflow-x: auto;
`;

export const FrameIdPill = styled.span`
  font-size: 0.85em;
  background: #e0e0e0;
  color: #555;
  border-radius: 10px;
  padding: 2px 10px;
  font-weight: 500;
`;

export const ModalImageCol = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  margin-top: 32px;
`;

export const ModalDropdownsCol = styled.div`
  display: flex;
  flex-direction: column;
  gap: 28px;
  justify-content: flex-start;
  align-items: flex-start;
  width: 100%;
  height: 100%;
  margin-top: -40px;
  margin-left: -32px;
`;

export const ModalImageButtonsRow = styled.div`
  margin-top: 18px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
`;
