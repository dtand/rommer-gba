import React, { createContext, useContext, useState, useRef } from 'react';
import { FrameContextResponse } from '../api/frameContext';
import { getFrameImage } from '../api/frameImage';
import { getFrameContexts, FrameContextFilter } from '../api/frameContexts';
import { useSessionContext } from './SessionContext';

export type FrameDataContextType = {
  frameImages: string[];
  setFrameImages: React.Dispatch<React.SetStateAction<string[]>>;
  frameContexts: FrameContextResponse[];
  setFrameContexts: React.Dispatch<React.SetStateAction<FrameContextResponse[]>>;
  currentFilter: FrameContextFilter;
  setFilter: (filter: FrameContextFilter) => Promise<void>;
  currentStartId: string;
  setCurrentStartId: React.Dispatch<React.SetStateAction<string>>;
  isLoading: boolean;
  isEndOfData: boolean;
  fetchFrames: (startId?: string, append?: boolean, filterOverride?: FrameContextFilter) => Promise<void>;
  handleLoadMore: () => void;
  resetState: () => void;
  endRangeValue: number | null;
  setEndRangeValue: React.Dispatch<React.SetStateAction<number | null>>;
  updateFrameContexts: (frameSetIds: string[], annotation: any) => void;
};

const FrameDataContext = createContext<FrameDataContextType | undefined>(undefined);

export const FrameDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [frameImages, setFrameImages] = useState<string[]>([]);
  const [frameContexts, setFrameContexts] = useState<FrameContextResponse[]>([]);
  const [currentFilter, setCurrentFilter] = useState<FrameContextFilter>('ALL');
  const [currentStartId, setCurrentStartId] = useState<string>('1');
  const [isLoading, setIsLoading] = useState(false);
  const [isEndOfData, setIsEndOfData] = useState(false);
  const [endRangeValue, setEndRangeValue] = useState<number | null>(null);
  const { session } = useSessionContext();
  const filterFetchRef = useRef(false);
  const lastFetchedStartId = useRef<string | null>(null);
  const pageSize = 50;

  // Reset state, but if custom range is set, keep currentStartId
  const resetState = () => {
    setFrameImages([]);
    setFrameContexts([]);
    setIsEndOfData(false);
    setIsLoading(false);
    setCurrentStartId('1');
  };

  // Fetch frames, respecting custom range if set
  const fetchFrames = async (startId: string = '1', append: boolean = false, filterOverride?: FrameContextFilter) => {
    if (!session?.id || isLoading || lastFetchedStartId.current === startId) {
      return;
    }
    lastFetchedStartId.current = startId;
    setIsLoading(true);
    const filterToUse = filterOverride || currentFilter;
    try {
      const frameContextsResp = await getFrameContexts(session.id, startId, pageSize, filterToUse);
      let contexts = frameContextsResp.contexts;
      // If custom range, filter out frames beyond endRangeValue
      if (endRangeValue !== null) {
        contexts = contexts.filter(ctx => Number(ctx.frame_set_id) <= endRangeValue);
      }
      if (contexts.length === 0) {
        if (startId === '1' || append) {
          setIsEndOfData(true);
        }
        setIsLoading(false);
        return;
      }
      // If last frame in batch is at or past endRangeValue, set isEndOfData
      if (
        contexts.length < pageSize ||
        (endRangeValue !== null && Number(contexts[contexts.length - 1].frame_set_id) >= endRangeValue)
      ) {
        setIsEndOfData(true);
      }
      const images: string[] = await Promise.all(
        contexts.map(async ctx => {
          try {
            const blob = await getFrameImage(session.id, ctx.frame_set_id);
            return URL.createObjectURL(blob);
          } catch {
            return '';
          }
        })
      );
      if (append) {
        setFrameImages(prev => [...prev, ...images]);
        setFrameContexts(prev => [...prev, ...contexts]);
      } else {
        setFrameImages(images);
        setFrameContexts(contexts);
      }
      if (contexts.length > 0) {
        setCurrentStartId(contexts[contexts.length - 1].frame_set_id + 1);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadMore = () => {
    if (isLoading || isEndOfData) return;
    fetchFrames(currentStartId, true);
  };

  const setFilter = async (newFilter: FrameContextFilter) => {
    if (filterFetchRef.current) return;
    filterFetchRef.current = true;
    setCurrentFilter(newFilter);
    resetState();
    setIsLoading(true);
    await fetchFrames(endRangeValue ? currentStartId : '1', false, newFilter);
    setIsLoading(false);
    filterFetchRef.current = false;
  };

  // Update frameContexts for a set of frame_set_ids
  const updateFrameContexts = (frameSetIds: string[], annotation: any) => {
    setFrameContexts(prev => prev.map(ctx =>
      frameSetIds.includes(ctx.frame_set_id)
        ? { ...ctx, annotations: { ...ctx.annotations, ...annotation } }
        : ctx
    ));
  };

  React.useEffect(() => {
    if (session?.id) {
      fetchFrames(currentStartId, false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session?.id, endRangeValue]);

  return (
    <FrameDataContext.Provider value={{
      frameImages,
      setFrameImages,
      frameContexts,
      setFrameContexts,
      currentFilter,
      setFilter,
      currentStartId,
      setCurrentStartId,
      isLoading,
      isEndOfData,
      fetchFrames,
      handleLoadMore,
      resetState,
      endRangeValue,
      setEndRangeValue,
      updateFrameContexts
    }}>
      {children}
    </FrameDataContext.Provider>
  );
};

export const useFrameDataContext = () => {
  const context = useContext(FrameDataContext);
  if (!context) throw new Error('useFrameDataContext must be used within a FrameDataProvider');
  return context;
};

export type FrameData = {
  context: FrameContextResponse | undefined;
  image: string | undefined;
};

// Helper function to get frame data by ID
export function getFrameDataById(frameContexts: FrameContextResponse[], frameImages: string[], id: string): FrameData {
  const idx = frameContexts.findIndex(ctx => ctx.frame_set_id === id);
  return {
    context: frameContexts[idx],
    image: frameImages[idx]
  };
}
