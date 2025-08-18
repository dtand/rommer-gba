import React from 'react';
import { ListingContainer, FrameIdPill } from './FrameIdListing.styled';

export type FrameIdListStyle = 'pill' | 'comma';

interface FrameIdListingProps {
  modalFrameIds: number[];
  listStyle?: FrameIdListStyle;
}

const FrameIdListing: React.FC<FrameIdListingProps> = ({ modalFrameIds, listStyle = 'pill' }) => {
  if (!Array.isArray(modalFrameIds) || modalFrameIds.length === 0) return null;

  if (listStyle === 'comma') {
    const idsToShow = modalFrameIds.slice(0, 10);
    const idsString = idsToShow.join(', ');
    return (
      <ListingContainer>
        <span>
          {idsString}
          {modalFrameIds.length > 10 ? ` +${modalFrameIds.length - 10} more` : ''}
        </span>
      </ListingContainer>
    );
  }

  // pill style (default)
  return (
    <ListingContainer>
      {modalFrameIds.slice(0, 10).map((frameId, idx) => (
        <FrameIdPill key={frameId || idx}>{frameId}</FrameIdPill>
      ))}
      {modalFrameIds.length > 10 && (
        <FrameIdPill>+{modalFrameIds.length - 10} more</FrameIdPill>
      )}
    </ListingContainer>
  );
};

export default FrameIdListing;
