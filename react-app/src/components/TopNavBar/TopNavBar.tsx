import React, { useState } from 'react';
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
import { SessionInfo } from '../../api/sessions';
import { CustomDropdown } from '../CustomDropdown/CustomDropdown';

interface TopNavBarProps {
  sessions: SessionInfo[];
  selectedSession: string;
  onSessionChange: (sessionId: string) => void;
  progress?: import('../../api/progress').ProgressResponse | null;
}

const filterOptions = [
  'All',
  'Annotated',
  'Partially Annotated',
  'Not Annotated'
];

const TopNavBar: React.FC<TopNavBarProps> = ({ sessions, selectedSession, onSessionChange, progress }) => {
  const [filter, setFilter] = useState('All');
  const session = sessions.find(s => s.session_id === selectedSession);
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
            options={sessions.map(s => s.session_id)}
            value={selectedSession}
            onChange={onSessionChange}
            style={{ minWidth: 320, maxWidth: 520, width: '100%' }}
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
