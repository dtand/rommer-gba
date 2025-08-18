import React, { useState, useEffect } from 'react';
import { GridWrapper, Grid, FrameItem, FrameImage, FramePlaceholder, FrameStatusIcon, FrameMetaRow } from './AnnotationGrid.styled';
import { useFrameDataContext } from '../../contexts/FrameDataContext';
import { useFrameSelection } from '../../contexts/FrameSelectionContext';
import { FrameContextResponse } from '../../api';
import { FaCheckCircle, FaRegCircle, FaExclamationCircle } from 'react-icons/fa';
import NextFrameBadge from '../NextFrameBadge/NextFrameBadge';

function getFrameStatus(context: FrameContextResponse) {
  const annotations = context?.annotations;
  if (!annotations || Object.keys(annotations).length === 0) return 'notAnnotated';
  if (annotations.complete === true) return 'complete';
  return 'partial';
}

const AnnotationGrid: React.FC = () => {
  const {
    frameImages,
    frameContexts,
    isEndOfData,
    handleLoadMore
  } = useFrameDataContext();
  const {
    setActiveFrameId,
    setSelectedFrameIds
  } = useFrameSelection();
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
  const [hovered, setHovered] = useState<number | null>(null);
  const gridRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Set active frame on hover or selection
    if (hovered !== null) {
      setActiveFrameId(frameContexts[hovered]?.frame_set_id || '');
    } else if (selectedIndices.length > 0) {
      const lastIdx = selectedIndices[selectedIndices.length - 1];
      setActiveFrameId(frameContexts[lastIdx]?.frame_set_id || '');
    } else {
      setActiveFrameId('');
    }
    // Update selectedFrameIds list
    setSelectedFrameIds(selectedIndices.map(idx => frameContexts[idx]?.frame_set_id).filter(Boolean));
  }, [hovered, selectedIndices, frameContexts, setActiveFrameId, setSelectedFrameIds]);

  // Clear selection when frame data changes
  useEffect(() => {
    setSelectedIndices([]);
    setActiveFrameId('');
    setSelectedFrameIds([]);
  }, [frameImages, frameContexts, setActiveFrameId, setSelectedFrameIds]);

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

  React.useEffect(() => {
    const handleScroll = () => {
      if (!gridRef.current || isEndOfData) return;
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
  }, [handleLoadMore, isEndOfData]);

  useEffect(() => {
    if (gridRef.current) {
      gridRef.current.scrollTop = 0;
    }
  }, []);

  // Find the index of the first non-annotated frame
  const firstNonAnnotatedIdx = frameContexts.findIndex(ctx => !ctx.annotations || Object.keys(ctx.annotations).length === 0 || ctx.annotations.complete !== true);

  return (
    <GridWrapper ref={gridRef}>
      {frameImages.length === 0 ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%' }}>
          <span style={{ color: '#bbb', fontSize: '1.5rem', fontWeight: 500 }}>No data for filter</span>
        </div>
      ) : ( <div>
        <Grid>
          {frameImages.map((img, i) => {
            const status = getFrameStatus(frameContexts[i] || {});
            let statusIcon = null;
            if (status === 'complete') {
              statusIcon = <FaCheckCircle style={{ color: '#28a745' }} title="Complete" />;
            } else if (status === 'partial') {
              statusIcon = <FaExclamationCircle style={{ color: '#ffc107' }} title="Partially Annotated" />;
            } else {
              statusIcon = <FaRegCircle style={{ color: '#bbb' }} title="Not Annotated" />;
            }
            const frameSetId = frameContexts[i]?.frame_set_id || '';
            return (
              <FrameItem
                key={i}
                $selected={selectedIndices.includes(i)}
                $hovered={hovered === i}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
                onClick={e => handleClick(i, e)}
                style={{ position: 'relative', flexDirection: 'column', justifyContent: 'flex-start' }}
              >
                {i === firstNonAnnotatedIdx && <NextFrameBadge />}
                {img ? (
                  <FrameImage src={img} alt={`Frame ${i + 1}`} />
                ) : (
                  <FramePlaceholder />
                )}
                <FrameMetaRow $complete={status === 'complete'} $partial={status === 'partial'}>
                  <span>Frame Set: {frameSetId}</span>
                  <span style={{ display: 'flex', alignItems: 'center', marginLeft: 4 }}>{statusIcon}</span>
                </FrameMetaRow>
              </FrameItem>
            );
          })}
        </Grid>
          <div style={{ height: 128 }} />
        </div>
      )}
    </GridWrapper>
  );
};

export default AnnotationGrid;
