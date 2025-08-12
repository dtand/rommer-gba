import React from 'react';
import { FaRegImage } from 'react-icons/fa';

interface FrameIdListingProps {
  selectedFrameIds: number[];
}

const FrameIdListing: React.FC<FrameIdListingProps> = ({ selectedFrameIds }) => (
  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center', marginBottom: '10px', maxWidth: '100%', overflowX: 'auto' }}>
    <FaRegImage size={18} style={{ color: '#888', marginRight: '2px' }} />
    {Array.isArray(selectedFrameIds) && selectedFrameIds.length > 0 && (
      <>
        {selectedFrameIds.slice(0, 10).map((frameId, idx) => (
          <span key={frameId || idx} style={{ fontSize: '0.85em', background: '#e0e0e0', color: '#555', borderRadius: '10px', padding: '2px 10px', fontWeight: 500 }}>
            {frameId}
          </span>
        ))}
        {selectedFrameIds.length > 12 && (
          <span style={{ fontSize: '0.85em', background: '#e0e0e0', color: '#555', borderRadius: '10px', padding: '2px 10px', fontWeight: 500 }}>
            +{selectedFrameIds.length - 10} more
          </span>
        )}
      </>
    )}
  </div>
);

export default FrameIdListing;
