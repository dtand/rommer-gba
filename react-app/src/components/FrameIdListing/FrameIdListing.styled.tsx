import styled from 'styled-components';

export const ListingContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 10px;
  max-width: 100%;
  overflow-x: auto;
`;

export const FrameIcon = styled.span`
  display: flex;
  align-items: center;
  margin-right: 2px;
  color: #888;
`;

export const FrameIdPill = styled.span`
  font-size: 0.85em;
  background: #e0e0e0;
  color: #555;
  border-radius: 10px;
  padding: 2px 10px;
  font-weight: 500;
`;
