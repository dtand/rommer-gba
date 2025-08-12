import React, { createContext, useContext, useState } from 'react';
import { FrameContextResponse } from '../api/frameContext';
import { getFrameImage } from '../api/frameImage';
import { getFrameContext } from '../api/frameContext';
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
  fetchFrames: (offset?: number, append?: boolean) => Promise<void>;
  handleLoadMore: () => void;
  isLoading: boolean;
  isBatchLoading: boolean;
  selectedFrameContexts: FrameContextResponse[];
  setSelectedFrameContexts: React.Dispatch<React.SetStateAction<FrameContextResponse[]>>;
};

const AnnotationContext = createContext<AnnotationContextType | undefined>(undefined);

export const AnnotationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [frameImages, setFrameImages] = useState<string[]>([]);
  const [frameContexts, setFrameContexts] = useState<FrameContextResponse[]>([]);
  const [frameOffset, setFrameOffset] = useState<number>(0);
  const [activeFrame, setActiveFrame] = useState<FrameContextResponse | null>(null);
  const [activeFrameImage, setActiveFrameImage] = useState<string | null>(null);
  const [activeFrameId, setActiveFrameId] = useState<number | null>(null);
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
  const [selectedFrameIds, setSelectedFrameIds] = useState<number[]>([]);
  const [selectedFrameContexts, setSelectedFrameContexts] = useState<FrameContextResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isBatchLoading, setIsBatchLoading] = useState(false);
  const { session } = useSessionContext();
  const FRAME_LOAD_COUNT = 50;

  const fetchFrames = async (offset = 0, append = false) => {
    if (!session?.id) return;
    setIsLoading(true);
    setIsBatchLoading(true);
    const totalFrames = session?.metadata?.total_frame_sets || 0;
    const frameCount = Math.min(FRAME_LOAD_COUNT, totalFrames - offset);
    const images: string[] = [];
    const contexts: FrameContextResponse[] = [];
    // Fetch all images and contexts in parallel for the batch
    await Promise.all([
      (async () => {
        for (let i = 1 + offset; i <= frameCount + offset; i++) {
          try {
            const blob = await getFrameImage(session.id, i.toString());
            images.push(URL.createObjectURL(blob));
          } catch {
            images.push('');
          }
        }
      })(),
      (async () => {
        for (let i = 1 + offset; i <= frameCount + offset; i++) {
          try {
            const context = await getFrameContext(session.id, i.toString());
            contexts.push(context);
          } catch {
            contexts.push({});
          }
        }
      })()
    ]);
    if (append) {
      setFrameImages(prev => [...prev, ...images]);
      setFrameContexts(prev => [...prev, ...contexts]);
    } else {
      setFrameImages(images);
      setFrameContexts(contexts);
    }
    setIsLoading(false);
    setIsBatchLoading(false);
  };

  const handleLoadMore = () => {
    const totalFrames = session?.metadata?.total_frame_sets || 0;
    if (frameOffset >= totalFrames || isLoading) return;
    fetchFrames(frameOffset, true);
    setFrameOffset(prev => prev + FRAME_LOAD_COUNT);
  };

  const initialLoadRef = React.useRef<string | null>(null);

  React.useEffect(() => {
    if (session?.id && initialLoadRef.current !== session.id) {
      initialLoadRef.current = session.id;
      setIsLoading(true);
      (async () => {
        await fetchFrames(0, false);
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
      isBatchLoading
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
