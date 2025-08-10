import React from 'react';

const AnnotationGrid: React.FC = () => (
  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: '16px', padding: '24px' }}>
    {/* Example grid items, replace with dynamic frame data */}
    {[...Array(12)].map((_, i) => (
      <div key={i} style={{ background: '#fff', border: '1px solid #ccc', borderRadius: '8px', padding: '12px', textAlign: 'center' }}>
        <img src="https://via.placeholder.com/120x90" alt={`Frame ${i + 1}`} style={{ marginBottom: '8px', borderRadius: '4px' }} />
        <div>Frame {i + 1}</div>
      </div>
    ))}
  </div>
);

export default AnnotationGrid;
