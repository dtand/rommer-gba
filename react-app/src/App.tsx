import React, { useEffect, useCallback, useState } from 'react';
import TopNavBar from './components/TopNavBar/TopNavBar';
import SideBar from './components/SideBar/SideBar';
import AnnotationGrid from './components/AnnotationGrid/AnnotationGrid';
import AnnotationsModal from './components/AnnotationsModal/AnnotationsModal';
import LoadingOverlay from './components/LoadingOverlay/LoadingOverlay';
import { getSessions, SessionsResponse, SessionInfo } from './api/sessions';
import { fetchAggregateFields } from './api/aggregateFields';
import { getProgress } from './api/progress';
import { AppContainer, MainContent, GridArea } from './App.styled';
import { SessionProvider, useSessionContext } from './contexts/SessionContext';
import { AnnotationProvider, useAnnotationContext } from './contexts/AnnotationContext';

const AppContent: React.FC = () => {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalAnnotations, setModalAnnotations] = useState<any>(null);
  const {
    session,
    setSession,
    progress,
    setProgress,
    annotationFields,
    setAnnotationFields
  } = useSessionContext();
  const {
    selectedIndices,
    setSelectedIndices,
    setActiveFrame,
    setActiveFrameImage,
    setActiveFrameId,
    setSelectedFrameIds,
    selectedFrameIds,
    frameContexts,
    setFrameContexts,
    activeFrame,
    activeFrameImage,
    activeFrameId,
    isBatchLoading
  } = useAnnotationContext();

  useEffect(() => {
    getSessions().then((data: SessionsResponse) => {
      setSessions(data.sessions || []);
      if (data.sessions && data.sessions.length > 0) {
        setSession({ id: data.sessions[0].session_id, metadata: data.sessions[0].metadata });
      }
    });
  }, [setSession]);

  useEffect(() => {
    if (session?.id) {
      fetchAggregateFields(session.id).then(setAnnotationFields);
      getProgress(session.id).then(setProgress);
      setSelectedIndices([]);
      setActiveFrame(null);
      setActiveFrameImage(null);
      setActiveFrameId(null);
      setModalAnnotations(null);
      setSelectedFrameIds([]);
      setIsModalOpen(false);
    }
  }, [session?.id, setAnnotationFields, setProgress, setSelectedIndices, setActiveFrame, setActiveFrameImage, setActiveFrameId, setModalAnnotations, setSelectedFrameIds]);

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
      {isBatchLoading && <LoadingOverlay />}
      <TopNavBar />
      <MainContent>
        <SideBar />
        <GridArea>
          <AnnotationGrid />
        </GridArea>
      </MainContent>
      <AnnotationsModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)}
      />
    </AppContainer>
  );
};

const App: React.FC = () => (
  <SessionProvider>
    <AnnotationProvider>
      <AppContent />
    </AnnotationProvider>
  </SessionProvider>
);

export default App;
