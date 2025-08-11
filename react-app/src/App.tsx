import React, { useState, useEffect, useCallback } from 'react';
import TopNavBar from './components/TopNavBar/TopNavBar';
import SideBar from './components/SideBar/SideBar';
import AnnotationGrid from './components/AnnotationGrid/AnnotationGrid';
import AnnotationsModal from './components/AnnotationsModal/AnnotationsModal';
import LoadingOverlay from './components/LoadingOverlay/LoadingOverlay';
import { getSessions, SessionsResponse, SessionInfo } from './api/sessions';
import { aggregateField, aggregateActions, AggregateFieldResponse, ActionsAggregateResponse } from './api/aggregateFields';
import { getFrameImage } from './api/frameImage';
import { getFrameContext, FrameContextResponse } from './api/frameContext';
import { getProgress, ProgressResponse } from './api/progress';
import { AppContainer, MainContent, GridArea } from './App.styled';

const FRAME_LOAD_COUNT = 50; // Maximum frames to load

function App() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>('');
  const [contextFields, setContextFields] = useState<AggregateFieldResponse | null>(null);
  const [sceneFields, setSceneFields] = useState<AggregateFieldResponse | null>(null);
  const [actionsAggregate, setActionsAggregate] = useState<ActionsAggregateResponse | null>(null);
  const [frameImages, setFrameImages] = useState<string[]>([]);
  const [frameContexts, setFrameContexts] = useState<FrameContextResponse[]>([]);
  const [frameOffset, setFrameOffset] = useState(0);
  const [activeFrame, setActiveFrame] = useState<FrameContextResponse | null>(null);
  const [activeFrameImage, setActiveFrameImage] = useState<string | null>(null);
  const [activeFrameId, setActiveFrameId] = useState<number | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalAnnotations, setModalAnnotations] = useState<any>(null);
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [modalFrameIds, setModalFrameIds] = useState<number[]>([]);
  const [progress, setProgress] = useState<ProgressResponse | null>(null);

  useEffect(() => {
    getSessions().then((data: SessionsResponse) => {
      setSessions(data.sessions || []);
      if (data.sessions && data.sessions.length > 0) {
        setSelectedSession(data.sessions[0].session_id);
      }
    });
  }, []);

  useEffect(() => {
    if (selectedSession) {
      aggregateField('context', selectedSession).then(setContextFields);
      aggregateField('scene', selectedSession).then(setSceneFields);
      aggregateActions(selectedSession).then(setActionsAggregate);
      getProgress(selectedSession).then(setProgress);
    }
  }, [selectedSession]);

  const fetchFrames = useCallback(async (offset = 0, append = false) => {
    setIsLoading(true);
    if (!selectedSession || !contextFields || !sceneFields || !actionsAggregate) {
      setIsLoading(false);
      return;
    }
    const session = sessions.find(s => s.session_id === selectedSession);
    const totalFrames = session?.metadata?.total_frame_sets || 0;
    const frameCount = Math.min(FRAME_LOAD_COUNT, totalFrames - offset);
    const images: string[] = [];
    for (let i = 1 + offset; i <= frameCount + offset; i++) {
      try {
        const blob = await getFrameImage(selectedSession, i.toString());
        images.push(URL.createObjectURL(blob));
      } catch {
        images.push('');
      }
    }
    const contexts: FrameContextResponse[] = [];
    for (let i = 1 + offset; i <= frameCount + offset; i++) {
      try {
        const context = await getFrameContext(selectedSession, i.toString());
        contexts.push(context);
      } catch {
        contexts.push({});
      }
    }
    if (append) {
      setFrameImages(prev => [...prev, ...images]);
      setFrameContexts(prev => [...prev, ...contexts]);
    } else {
      setFrameImages(images);
      setFrameContexts(contexts);
    }
    setIsLoading(false);
  }, [selectedSession, contextFields, sceneFields, actionsAggregate, sessions]);

  useEffect(() => {
    fetchFrames(0, false);
    setFrameOffset(FRAME_LOAD_COUNT);
  }, [fetchFrames]);

  const handleLoadMore = useCallback(() => {
    const session = sessions.find(s => s.session_id === selectedSession);
    const totalFrames = session?.metadata?.total_frame_sets || 0;
    if (frameOffset >= totalFrames) return;
    fetchFrames(frameOffset, true);
    setFrameOffset(prev => prev + FRAME_LOAD_COUNT);
  }, [frameOffset, fetchFrames, selectedSession, contextFields, sceneFields, actionsAggregate, sessions]);

  // Callback to set active frame and image from AnnotationGrid
  const handleActiveFrameChange = useCallback((frame: FrameContextResponse | null, image?: string | null, index?: number | null) => {
    setActiveFrame(frame);
    setActiveFrameImage(image || null);
    setActiveFrameId(index != null ? index + 1 : null);
  }, []);

  // Show modal on Enter key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        // Gather all selected context data
        const selectedContexts = selectedIndices.map(idx => frameContexts[idx]);
        const selectedFrameIds = selectedIndices.map(idx => {
          const ctx = frameContexts[idx];
          return ctx?.frame_id ?? (idx + 1);
        });
        setModalAnnotations(selectedContexts);
        setModalFrameIds(selectedFrameIds);
        setIsModalOpen(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedIndices, frameContexts]);

  return (
    <AppContainer>
      {isLoading && <LoadingOverlay />}
      <TopNavBar
        sessions={sessions}
        selectedSession={selectedSession}
        onSessionChange={setSelectedSession}
        progress={progress}
      />
      <MainContent>
        <SideBar activeFrame={activeFrame} activeFrameImage={activeFrameImage} activeFrameId={activeFrameId} />
        <GridArea>
          <AnnotationGrid
            frameImages={frameImages}
            frameContexts={frameContexts}
            onActiveFrameChange={handleActiveFrameChange}
            onSelectionChange={setSelectedIndices}
            onLoadMore={handleLoadMore}
          />
        </GridArea>
      </MainContent>
      <AnnotationsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        annotations={modalAnnotations}
        modalFrameIds={modalFrameIds}
        activeFrame={activeFrame}
        activeFrameImage={activeFrameImage}
        contextFields={contextFields}
        sceneFields={sceneFields}
        actionsAggregate={actionsAggregate}
      />
    </AppContainer>
  );
}

export default App;
