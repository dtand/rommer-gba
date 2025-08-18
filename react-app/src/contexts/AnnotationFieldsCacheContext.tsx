import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

export interface AnnotationFields {
  contexts: string[];
  scenes: string[];
  tags: string[];
  actions: string[];
  intents: string[];
  outcomes: string[];
  // Add more fields as needed
}

interface AnnotationFieldsCache {
  [gameName: string]: AnnotationFields;
}

interface AnnotationFieldsCacheContextType {
  getFields: (gameName: string) => AnnotationFields | undefined;
  mergeFields: (gameName: string, newFields: AnnotationFields) => void;
  setFields: (gameName: string, fields: AnnotationFields) => void;
}

const AnnotationFieldsCacheContext = createContext<AnnotationFieldsCacheContextType | undefined>(undefined);

export const useAnnotationFieldsCache = () => {
  const ctx = useContext(AnnotationFieldsCacheContext);
  if (!ctx) throw new Error('useAnnotationFieldsCache must be used within AnnotationFieldsCacheProvider');
  return ctx;
};

function mergeAnnotationFields(a: AnnotationFields, b: AnnotationFields): AnnotationFields {
  // Merge and sort all arrays for each field
  return {
    contexts: Array.from(new Set([...(a.contexts || []), ...(b.contexts || [])])).sort(),
    scenes: Array.from(new Set([...(a.scenes || []), ...(b.scenes || [])])).sort(),
    tags: Array.from(new Set([...(a.tags || []), ...(b.tags || [])])).sort(),
    actions: Array.from(new Set([...(a.actions || []), ...(b.actions || [])])).sort(),
    intents: Array.from(new Set([...(a.intents || []), ...(b.intents || [])])).sort(),
    outcomes: Array.from(new Set([...(a.outcomes || []), ...(b.outcomes || [])])).sort(),
  };
}

export const AnnotationFieldsCacheProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cache, setCache] = useState<AnnotationFieldsCache>({});

  const getFields = useCallback((gameName: string) => cache[gameName], [cache]);

  const mergeFields = useCallback((gameName: string, newFields: AnnotationFields) => {
    setCache(prev => ({
      ...prev,
      [gameName]: prev[gameName] ? mergeAnnotationFields(prev[gameName], newFields) : newFields,
    }));
  }, []);

  const setFields = useCallback((gameName: string, fields: AnnotationFields) => {
    setCache(prev => ({ ...prev, [gameName]: fields }));
  }, []);

  // Optionally, persist cache to localStorage here

  return (
    <AnnotationFieldsCacheContext.Provider value={{ getFields, mergeFields, setFields }}>
      {children}
    </AnnotationFieldsCacheContext.Provider>
  );
};
