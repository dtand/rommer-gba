import React, { useState, useEffect } from 'react';
import { GridWrapper, Grid, FrameItem, FrameImage, FramePlaceholder } from './AnnotationGrid.styled';
import { useAnnotationContext } from '../../contexts/AnnotationContext';

// Removed all callback props
function getFrameStatus(context) {
  const annotations = context?.annotations;
  if (!annotations || Object.keys(annotations).length === 0) return 'notAnnotated';
  if (annotations.complete === true) return 'complete';
  return 'partial';
}

const AnnotationGrid: React.FC = () => {
  const {
    frameImages,
    frameContexts,
    selectedIndices,
    isEndOfData,
    setSelectedIndices,
    setActiveFrame,
    setActiveFrameImage,
    setActiveFrameId,
    handleLoadMore
  } = useAnnotationContext();
  const [hovered, setHovered] = useState<number | null>(null);
  const gridRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Set active frame and image on hover or selection
    if (hovered !== null) {
      setActiveFrame(frameContexts[hovered] || null);
      setActiveFrameImage(frameImages[hovered] || null);
      setActiveFrameId(hovered + 1);
    } else if (selectedIndices.length > 0) {
      const lastIdx = selectedIndices[selectedIndices.length - 1];
      setActiveFrame(frameContexts[lastIdx] || null);
      setActiveFrameImage(frameImages[lastIdx] || null);
      setActiveFrameId(lastIdx + 1);
    } else {
      setActiveFrame(null);
      setActiveFrameImage(null);
      setActiveFrameId(null);
    }
  }, [hovered, selectedIndices, frameContexts, frameImages, setActiveFrame, setActiveFrameImage, setActiveFrameId]);

  // Shift+Click range select
  const handleClick = (idx: number, e: React.MouseEvent) => {
    let newSelected: number[];
    if (e.shiftKey && selectedIndices.length > 0) {
      const last = selectedIndices[selectedIndices.length - 1];
      const [start, end] = [Math.min(last, idx), Math.max(last, idx)];
      const range = Array.from({ length: end - start + 1 }, (_, i) => start + i);
      newSelected = Array.from(new Set([...selectedIndices, ...range]));
    } else {
      newSelected = selectedIndices.includes(idx)
        ? selectedIndices.filter(i => i !== idx)
        : [...selectedIndices, idx];
    }
    setSelectedIndices(newSelected);
  };

  // Remove fetchFrames logic, note: loading more frames should be handled via context or another mechanism
  React.useEffect(() => {
    const handleScroll = () => {
      if (!gridRef.current) return;
      const { scrollTop, scrollHeight, clientHeight } = gridRef.current;
      if (scrollTop + clientHeight >= scrollHeight - 40) {
        handleLoadMore();
      }
    };
    const gridEl = gridRef.current;
    if (gridEl) gridEl.addEventListener('scroll', handleScroll);
    return () => {
      if (gridEl) gridEl.removeEventListener('scroll', handleScroll);
    };
  }, [handleLoadMore]);

  React.useEffect(() => {
    if (!gridRef.current) return;
    const { scrollHeight, clientHeight } = gridRef.current;
    if (scrollHeight <= clientHeight && !isEndOfData) {
      handleLoadMore();
    }
  }, [frameImages.length, frameContexts.length, handleLoadMore]);

  // Only scroll to top when session changes
  useEffect(() => {
    if (gridRef.current) {
      gridRef.current.scrollTop = 0;
    }
  }, []);

  return (
    <GridWrapper ref={gridRef}>
      {frameImages.length === 0 ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
          <span style={{ color: '#bbb', fontSize: '1.5rem', fontWeight: 500 }}>No data for filter</span>
        </div>
      ) : (
        <Grid>
          {frameImages.map((img, i) => {
            const status = getFrameStatus(frameContexts[i] || {});
            return (
              <FrameItem
                key={i}
                $selected={selectedIndices.includes(i)}
                $hovered={hovered === i}
                $complete={status === 'complete'}
                $partial={status === 'partial'}
                $notAnnotated={status === 'notAnnotated'}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
                onClick={e => handleClick(i, e)}
              >
                {img ? (
                  <FrameImage src={img} alt={`Frame ${i + 1}`} />
                ) : (
                  <FramePlaceholder />
                )}
              </FrameItem>
            );
          })}
        </Grid>
      )}
      <div style={{ height: 128 }} />
    </GridWrapper>
  );
};

export default AnnotationGrid;
