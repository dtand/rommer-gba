import React, { createContext, useContext, useState } from 'react';

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

export type SessionContextType = {
  session: SessionType | null;
  setSession: (session: SessionType | null) => void;
  progress: ProgressType | null;
  setProgress: (progress: ProgressType | null) => void;
  annotationFields: any;
  setAnnotationFields: (fields: any) => void;
};

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<SessionType | null>(null);
  const [progress, setProgress] = useState<ProgressType | null>(null);
  const [annotationFields, setAnnotationFields] = useState<any>(null);

  return (
    <SessionContext.Provider value={{ session, setSession, progress, setProgress, annotationFields, setAnnotationFields }}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSessionContext = () => {
  const context = useContext(SessionContext);
  if (!context) throw new Error('useSessionContext must be used within a SessionProvider');
  return context;
};
