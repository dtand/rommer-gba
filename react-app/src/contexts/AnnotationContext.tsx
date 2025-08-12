import React, { createContext, useContext, useState } from 'react';
import { FrameContextResponse } from '../api/frameContext';
import { getFrameImage } from '../api/frameImage';
import { getFrameContexts, FrameContextFilter } from '../api/frameContexts';
import { useSessionContext } from './SessionContext';

export type AnnotationContextType = {
  frameImages: string[];
  setFrameImages: React.Dispatch<React.SetStateAction<string[]>>;
  frameContexts: FrameContextResponse[];
  setFrameContexts: React.Dispatch<React.SetStateAction<FrameContextResponse[]>>;
  frameOffset: number;
  setFrameOffset: React.Dispatch<React.SetStateAction<number>>;
  activeFrame: FrameContextResponse | null;
  setActiveFrame: React.Dispatch<React.SetStateAction<FrameContextResponse | null>>;
  activeFrameImage: string | null;
  setActiveFrameImage: React.Dispatch<React.SetStateAction<string | null>>;
  activeFrameId: number | null;
  setActiveFrameId: React.Dispatch<React.SetStateAction<number | null>>;
  selectedIndices: number[];
  setSelectedIndices: React.Dispatch<React.SetStateAction<number[]>>;
  selectedFrameIds: number[];
  setSelectedFrameIds: React.Dispatch<React.SetStateAction<number[]>>;
  fetchFrames: (startId?: string, append?: boolean) => Promise<void>;
  handleLoadMore: () => void;
  isLoading: boolean;
  isBatchLoading: boolean;
  isEndOfData: boolean;
  selectedFrameContexts: FrameContextResponse[];
  setSelectedFrameContexts: React.Dispatch<React.SetStateAction<FrameContextResponse[]>>;
  setFilter: (filter: FrameContextFilter) => void;
  currentFilter: FrameContextFilter;
};

const AnnotationContext = createContext<AnnotationContextType | undefined>(undefined);

export const AnnotationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [frameImages, setFrameImages] = useState<string[]>([]);
  const [frameContexts, setFrameContexts] = useState<FrameContextResponse[]>([]);
  const [frameOffset, setFrameOffset] = useState<number>(0);
  const [currentStartId, setCurrentStartId] = useState<string>('1');
  const [currentFilter, setCurrentFilter] = useState<FrameContextFilter>('ALL');
  const [activeFrame, setActiveFrame] = useState<FrameContextResponse | null>(null);
  const [activeFrameImage, setActiveFrameImage] = useState<string | null>(null);
  const [activeFrameId, setActiveFrameId] = useState<number | null>(null);
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
  const [selectedFrameIds, setSelectedFrameIds] = useState<number[]>([]);
  const [selectedFrameContexts, setSelectedFrameContexts] = useState<FrameContextResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isBatchLoading, setIsBatchLoading] = useState(false);
  const [isEndOfData, setIsEndOfData] = useState(false);
  const { session } = useSessionContext();
  const FRAME_LOAD_COUNT = 50;

  const fetchFrames = async (startId: string = '1', append: boolean = false, filterOverride?: FrameContextFilter) => {
    if (!session?.id) return;
    setIsLoading(true);
    setIsBatchLoading(true);
    setIsEndOfData(false);
    const pageSize = 50;
    const filterToUse = filterOverride || currentFilter;
    try {
      const frameContextsResp = await getFrameContexts(session.id, startId, pageSize, filterToUse);
      const contexts = frameContextsResp.contexts;

      
      // API returned no data at all, this filter has no data
      if (contexts.length === 0 && startId === '1') {
        resetState();
        setIsEndOfData(true);
        setIsLoading(false);
        setIsBatchLoading(false);
        return;
      }

      // API returned no data for this batch, but there are more frames to load
      else if (contexts.length === 0) {
        setIsEndOfData(true);
        setIsLoading(false);
        setIsBatchLoading(false);
        return;
      }

      // API returned data, but the length is less than pageSize
      // This means we have reached the end of available data for this filter
      else if(contexts.length < pageSize){
        setIsEndOfData(true);
      }
      
      // Fetch images for each frame_set_id
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
      // Always update currentStartId to the frame_id of the last frame in the batch
      if (contexts.length > 0) {
        setCurrentStartId(contexts[contexts.length - 1].frame_set_id);
      }
    } finally {
      setIsLoading(false);
      setIsBatchLoading(false);
    }
  };

  const handleLoadMore = () => {
    if (isLoading) return;
    fetchFrames(currentStartId, true);
  };

  // Guard to prevent multiple fetches
  const filterFetchRef = React.useRef(false);

  const resetState = () => {
    setFrameImages([]);
    setFrameContexts([]);
    setCurrentStartId('1');
    setFrameOffset(0);
    setActiveFrame(null);
    setActiveFrameImage(null);
    setActiveFrameId(null);
    setSelectedIndices([]);
    setSelectedFrameIds([]);
    setSelectedFrameContexts([]);
    setIsEndOfData(false);
    setIsLoading(false);
    setIsBatchLoading(false);
  };

  const setFilter = async (newFilter: FrameContextFilter) => {
    if (filterFetchRef.current) return;
    filterFetchRef.current = true;
    setCurrentFilter(newFilter);
    resetState();
    setIsLoading(true);
    setIsBatchLoading(true);
    await fetchFrames('1', false, newFilter);
    setIsLoading(false);
    setIsBatchLoading(false);
    filterFetchRef.current = false;
  };

  const initialLoadRef = React.useRef<string | null>(null);

  React.useEffect(() => {
    if (session?.id && initialLoadRef.current !== session.id) {
      initialLoadRef.current = session.id;
      setIsLoading(true);
      (async () => {
        await fetchFrames('1', false);
        setFrameOffset(FRAME_LOAD_COUNT);
        setIsLoading(false);
      })();
    } else if (!session?.id) {
      initialLoadRef.current = null;
      setFrameImages([]);
      setFrameContexts([]);
      setFrameOffset(0);
      setIsLoading(false);
    }
  }, [session?.id]);

  React.useEffect(() => {
    // Update selectedFrameContexts whenever selectedIndices or frameContexts change
    setSelectedFrameContexts(selectedIndices.map(idx => frameContexts[idx]));
  }, [selectedIndices, frameContexts]);

  return (
    <AnnotationContext.Provider value={{
      frameImages, setFrameImages,
      frameContexts, setFrameContexts,
      frameOffset, setFrameOffset,
      activeFrame, setActiveFrame,
      activeFrameImage, setActiveFrameImage,
      activeFrameId, setActiveFrameId,
      selectedIndices, setSelectedIndices,
      selectedFrameIds, setSelectedFrameIds,
      selectedFrameContexts, setSelectedFrameContexts,
      
      fetchFrames,
      handleLoadMore,
      isLoading,
      isBatchLoading,
      isEndOfData,
      setFilter,
      currentFilter
    }}>
      {children}
    </AnnotationContext.Provider>
  );
};

export const useAnnotationContext = () => {
  const context = useContext(AnnotationContext);
  if (!context) throw new Error('useAnnotationContext must be used within an AnnotationProvider');
  return context;
};
