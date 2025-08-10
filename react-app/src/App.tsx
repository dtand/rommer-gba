import React, { useState, useEffect } from 'react';
import TopNavBar from './components/TopNavBar/TopNavBar';
import SideBar from './components/SideBar/SideBar';
import AnnotationGrid from './components/AnnotationGrid/AnnotationGrid';
import { getSessions, SessionsResponse, SessionInfo } from './api/sessions';
import { aggregateField, aggregateActions, AggregateFieldResponse, ActionsAggregateResponse } from './api/aggregateFields';

function App() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [selectedSession, setSelectedSession] = useState<string>('');
  const [contextFields, setContextFields] = useState<AggregateFieldResponse | null>(null);
  const [sceneFields, setSceneFields] = useState<AggregateFieldResponse | null>(null);
  const [actionsAggregate, setActionsAggregate] = useState<ActionsAggregateResponse | null>(null);

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
    }
  }, [selectedSession]);

  return (
    <div>
      <TopNavBar sessions={sessions} selectedSession={selectedSession} onSessionChange={setSelectedSession} />
      <SideBar/>
      <AnnotationGrid/>
    </div>
  );
}

export default App;
