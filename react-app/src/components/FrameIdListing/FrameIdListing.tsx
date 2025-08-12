import React from 'react';
import { FaRegImage } from 'react-icons/fa';

interface FrameIdListingProps {
  modalFrameIds: number[];
}

const FrameIdListing: React.FC<FrameIdListingProps> = ({ modalFrameIds }) => (
  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center', marginBottom: '10px', maxWidth: '100%', overflowX: 'auto' }}>
    <FaRegImage size={18} style={{ color: '#888', marginRight: '2px' }} />
    {Array.isArray(modalFrameIds) && modalFrameIds.length > 0 && (
      <>
        {modalFrameIds.slice(0, 10).map((frameId, idx) => (
          <span key={frameId || idx} style={{ fontSize: '0.85em', background: '#e0e0e0', color: '#555', borderRadius: '10px', padding: '2px 10px', fontWeight: 500 }}>
            {frameId}
          </span>
        ))}
        {modalFrameIds.length > 12 && (
          <span style={{ fontSize: '0.85em', background: '#e0e0e0', color: '#555', borderRadius: '10px', padding: '2px 10px', fontWeight: 500 }}>
            +{modalFrameIds.length - 10} more
          </span>
        )}
      </>
    )}
  </div>
);

export default FrameIdListing;
