import React, { useState, useEffect } from 'react';
import { GridWrapper, Grid, FrameItem, FrameImage, FramePlaceholder } from './AnnotationGrid.styled';
import { FrameContextResponse } from '../../api/frameContext';

interface AnnotationGridProps {
  frameImages: string[];
  frameContexts: FrameContextResponse[];
  onActiveFrameChange: (frame: FrameContextResponse | null, image?: string | null, index?: number | null) => void;
  onSelectionChange?: (selectedIndices: number[]) => void;
  onLoadMore?: () => void;
}

function getFrameStatus(context: FrameContextResponse): 'complete' | 'partial' | 'notAnnotated' {
  const annotations = context?.annotations;
  if (!annotations || Object.keys(annotations).length === 0) return 'notAnnotated';
  if (annotations.complete === true) return 'complete';
  return 'partial';
}

const AnnotationGrid: React.FC<AnnotationGridProps> = ({ frameImages, frameContexts, onActiveFrameChange, onSelectionChange, onLoadMore }) => {
  const [selected, setSelected] = useState<number[]>([]);
  const [hovered, setHovered] = useState<number | null>(null);
  const gridRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Set active frame and image on hover or selection
    if (hovered !== null) {
      onActiveFrameChange(frameContexts[hovered] || null, frameImages[hovered] || null, hovered + 1);
    } else if (selected.length > 0) {
      const lastIdx = selected[selected.length - 1];
      onActiveFrameChange(frameContexts[lastIdx] || null, frameImages[lastIdx] || null, lastIdx + 1);
    } else {
      onActiveFrameChange(null, null, null);
    }
  }, [hovered, selected, frameContexts, frameImages, onActiveFrameChange]);

  useEffect(() => {
    if (onSelectionChange) {
      onSelectionChange(selected);
    }
  }, [selected, onSelectionChange]);

  // Shift+Click range select
  const handleClick = (idx: number, e: React.MouseEvent) => {
    if (e.shiftKey && selected.length > 0) {
      const last = selected[selected.length - 1];
      const [start, end] = [Math.min(last, idx), Math.max(last, idx)];
      const range = Array.from({ length: end - start + 1 }, (_, i) => start + i);
      setSelected(prev => Array.from(new Set([...prev, ...range])));
    } else {
      setSelected(prev => prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]);
    }
  };

  React.useEffect(() => {
    const handleScroll = () => {
      if (!gridRef.current) return;
      const { scrollTop, scrollHeight, clientHeight } = gridRef.current;
      if (scrollTop + clientHeight >= scrollHeight - 40) {
        if (onLoadMore) onLoadMore();
      }
    };
    const gridEl = gridRef.current;
    if (gridEl) gridEl.addEventListener('scroll', handleScroll);
    return () => {
      if (gridEl) gridEl.removeEventListener('scroll', handleScroll);
    };
  }, [onLoadMore]);

  // Trigger load more if grid is not scrollable (content height <= container height)
  React.useEffect(() => {
    if (!gridRef.current || !onLoadMore) return;
    const { scrollHeight, clientHeight } = gridRef.current;
    if (scrollHeight <= clientHeight) {
      onLoadMore();
    }
  }, [frameImages.length, frameContexts.length, onLoadMore]);


  return (
    <GridWrapper ref={gridRef}>
      <Grid>
        {frameImages.map((img, i) => {
          const status = getFrameStatus(frameContexts[i] || {});
          return (
            <FrameItem
              key={i}
              $selected={selected.includes(i)}
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
      <div style={{ height: 128 }} />
    </GridWrapper>
  );
};

export default AnnotationGrid;
