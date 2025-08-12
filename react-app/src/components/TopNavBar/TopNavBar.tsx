import React, { useState, useEffect } from 'react';
import {
  NavBar,
  Row,
  Button,
  LeftGroup,
  RightGroup,
  Icon,
  SecondRow,
  GameName,
  Pill,
  ProgressText,
  ProgressBarContainer,
  ProgressBarFill,
  MemoryButton,
  LogoImage
} from './TopNavBar.styled';
import { FaLayerGroup, FaDatabase, FaFilter, FaFolderOpen, FaCheckCircle, FaSearch, FaMemory } from 'react-icons/fa';
import { MdDoneAll } from 'react-icons/md';
import { useSessionContext } from '../../contexts/SessionContext';
import { CustomDropdown } from '../CustomDropdown/CustomDropdown';

const filterOptions = [
  'All',
  'Annotated',
  'Partially Annotated',
  'Not Annotated'
];

const TopNavBar: React.FC = () => {
  const { session, setSession, progress } = useSessionContext();
  const [filter, setFilter] = useState('All');
  // Use sessions from AppContent state via local state
  const [sessions, setSessions] = useState<any[]>([]);
  useEffect(() => {
    // Fetch sessions on mount
    import('../../api/sessions').then(({ getSessions }) => {
      getSessions().then((data: any) => {
        setSessions(data.sessions || []);
      });
    });
  }, []);
  const selectedSession = session?.id || '';
  const gameName = session?.metadata?.game_name || 'Unknown';
  const totalFrames = session?.metadata?.total_frame_sets || 1;
  const complete = progress?.complete ?? 0;
  const partial = progress?.partial ?? 0;
  const percent = Math.round((complete / totalFrames) * 100);

  return (
    <NavBar>
      <Row>
        <LeftGroup>
          <LogoImage src="/rommer-gba.png" alt="Logo" />
          <CustomDropdown
            label="Sessions"
            options={sessions.map((s: any) => s.session_id)}
            value={selectedSession}
            onChange={id => {
              const found = sessions.find((s: any) => s.session_id === id);
              setSession(found ? { id: found.session_id, metadata: found.metadata } : null);
            }}
          />
          <CustomDropdown
            label="Filters"
            options={filterOptions}
            value={filter}
            onChange={setFilter}
          />
        </LeftGroup>
        <RightGroup>
          <Button><Icon><MdDoneAll /></Icon>Apply All</Button>
          <Button><Icon><FaDatabase /></Icon>Inject to DB</Button>
          <Button><Icon><FaCheckCircle /></Icon>Validate</Button>
          <Button><Icon><FaSearch /></Icon>Review</Button>
          <MemoryButton onClick={() => window.location.href = '/memory-analysis'}>
            <Icon><FaMemory /></Icon>Memory
          </MemoryButton>
        </RightGroup>
      </Row>
      <SecondRow>
        <GameName>{gameName}</GameName>
        <Pill color="#4caf50">Complete: {complete}</Pill>
        <Pill color="#ffc107">Partially Complete: {partial}</Pill>
        <ProgressText>{complete} / {totalFrames} ({percent}%)</ProgressText>
        <ProgressBarContainer>
          <ProgressBarFill percent={percent} />
        </ProgressBarContainer>
      </SecondRow>
    </NavBar>
  );
};

export default TopNavBar;
