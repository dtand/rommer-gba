import React, { useEffect, useState } from 'react';
import TopNavBar from './components/TopNavBar/TopNavBar';
import SideBar from './components/SideBar/SideBar';
import AnnotationGrid from './components/AnnotationGrid/AnnotationGrid';
import AnnotationsModal from './components/AnnotationsModal/AnnotationsModal';
import LoadingOverlay from './components/LoadingOverlay/LoadingOverlay';
import { getSessions, SessionsResponse } from './api/sessions';
import { fetchAggregateFields } from './api/aggregateFields';
import { getProgress } from './api/progress';
import { AppContainer, MainContent, GridArea } from './App.styled';
import { AnnotationFieldsCacheProvider } from './contexts/AnnotationFieldsCacheContext';
import { SessionProvider, useSessionContext } from './contexts/SessionContext';
import { FrameDataProvider, useFrameDataContext } from './contexts/FrameDataContext';
import { FrameSelectionProvider } from './contexts/FrameSelectionContext';

const AppContent: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const {
    session,
    setSession,
    setProgress,
    setAnnotationFields
  } = useSessionContext();
  const { isLoading } = useFrameDataContext();

  useEffect(() => {
    getSessions().then((data: SessionsResponse) => {
      if (data.sessions && data.sessions.length > 0) {
        setSession({ id: data.sessions[0].session_id, metadata: data.sessions[0].metadata });
      }
    });
  }, [setSession]);

  useEffect(() => {
    if (session?.id) {
      fetchAggregateFields(session.id).then(setAnnotationFields);
      getProgress(session.id).then(setProgress);
      setIsModalOpen(false);
    }
  }, [session?.id]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        setIsModalOpen(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <AppContainer>
      <TopNavBar />
      <MainContent>
        <SideBar />
        <GridArea>
          <AnnotationGrid />
        </GridArea>
      </MainContent>
      <AnnotationsModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
      {isLoading && <LoadingOverlay />}
    </AppContainer>
  );
};

const AllProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AnnotationFieldsCacheProvider>
    <SessionProvider>
      <FrameDataProvider>
        <FrameSelectionProvider>
          {children}
        </FrameSelectionProvider>
      </FrameDataProvider>
    </SessionProvider>
  </AnnotationFieldsCacheProvider>
);

const App: React.FC = () => (
  <AllProviders>
    <AppContent />
  </AllProviders>
);

export default App;
