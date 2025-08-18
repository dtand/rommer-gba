import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAnnotationFieldsCache } from './AnnotationFieldsCacheContext';

export type SessionType = {
  id: string;
  metadata: any;
  // Add other session fields as needed
};

export type ProgressType = {
  total: number;
  complete: number;
  partial: number;
};

export type RecentAnnotationFields = {
  contexts: string[];
  scenes: string[];
  tags: string[];
};

export type SessionContextType = {
  session: SessionType | null;
  setSession: (session: SessionType | null) => void;
  progress: ProgressType | null;
  setProgress: (progress: ProgressType | null) => void;
  annotationFields: any;
  setAnnotationFields: (fields: any) => void;
  recentAnnotationFields: RecentAnnotationFields;
  updateRecentFields: (type: 'contexts' | 'scenes' | 'tags', value: string) => void;
  previousAnnotation: any | null;
  setPreviousAnnotation: (annotation: any | null) => void;
};

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<SessionType | null>(null);
  const [progress, setProgress] = useState<ProgressType | null>(null);
  const [annotationFields, setAnnotationFieldsState] = useState<any>(null);
  const { mergeFields } = useAnnotationFieldsCache();

  const [recentAnnotationFields, setRecentAnnotationFields] = useState<RecentAnnotationFields>({
    contexts: [],
    scenes: [],
    tags: [],
  });

  const [previousAnnotation, setPreviousAnnotation] = useState<any | null>(null);

  const updateRecentFields = (type: 'contexts' | 'scenes' | 'tags', value: string) => {
    setRecentAnnotationFields(prev => {
      const limit = type === 'tags' ? 18 : 5;
      const filtered = prev[type].filter(v => v !== value);
      return {
        ...prev,
        [type]: [value, ...filtered].slice(0, limit),
      };
    });
  };

  // Wrap setAnnotationFields to also update the global cache by game name
  const setAnnotationFields = (fields: any) => {
    setAnnotationFieldsState(fields);
    if (session && session.metadata && session.metadata.game_name && fields) {
      mergeFieldsSorted(session.metadata.game_name, fields);
    }
  };

  // Helper to merge and sort all lists (sorting now handled in cache context)
  const mergeFieldsSorted = (gameName: string, newFields: any) => {
    mergeFields(gameName, newFields);
  };

  // If session changes, and annotationFields is set, update cache
  useEffect(() => {
    if (session && session.metadata && session.metadata.game_name && annotationFields) {
      mergeFieldsSorted(session.metadata.game_name, annotationFields);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session]);

  return (
    <SessionContext.Provider value={{ session, setSession, progress, setProgress, annotationFields, setAnnotationFields, recentAnnotationFields, updateRecentFields, previousAnnotation, setPreviousAnnotation }}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSessionContext = () => {
  const context = useContext(SessionContext);
  if (!context) throw new Error('useSessionContext must be used within a SessionProvider');
  return context;
};
