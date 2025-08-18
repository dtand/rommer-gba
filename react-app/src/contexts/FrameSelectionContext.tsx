import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface FrameSelectionContextType {
  activeFrameId: string;
  setActiveFrameId: (frameId: string) => void;
  selectedFrameIds: string[];
  setSelectedFrameIds: (frameIds: string[]) => void;
}

const FrameSelectionContext = createContext<FrameSelectionContextType | undefined>(undefined);

export const FrameSelectionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [activeFrameId, setActiveFrameId] = useState<string>(''); // Initialize with an empty string
  const [selectedFrameIds, setSelectedFrameIds] = useState<string[]>([]);

  return (
    <FrameSelectionContext.Provider value={{ activeFrameId, setActiveFrameId, selectedFrameIds, setSelectedFrameIds }}>
      {children}
    </FrameSelectionContext.Provider>
  );
};

export const useFrameSelection = (): FrameSelectionContextType => {
  const context = useContext(FrameSelectionContext);
  if (!context) {
    throw new Error('useFrameSelection must be used within a FrameSelectionProvider');
  }
  return context;
};
