import React from 'react';
import { NavBar, Logo, Row, Dropdown, Button, LeftGroup, RightGroup, Icon } from './TopNavBar.styled';
import { FaLayerGroup, FaDatabase, FaFilter, FaFolderOpen, FaCheckCircle, FaSearch, FaMemory } from 'react-icons/fa';
import { MdDoneAll } from 'react-icons/md';
import { SessionInfo } from '../../api/sessions';

interface TopNavBarProps {
  sessions: SessionInfo[];
  selectedSession: string;
  onSessionChange: (sessionId: string) => void;
}

const TopNavBar: React.FC<TopNavBarProps> = ({ sessions, selectedSession, onSessionChange }) => (
  <NavBar>
    <Row>
      <LeftGroup>
        <Logo>
          <img src="/logo.png" alt="Logo" style={{ height: 128, width: 128, marginRight: 8 }} />
        </Logo>
        <Dropdown value={selectedSession} onChange={e => onSessionChange(e.target.value)}>
          {sessions.map(session => (
            <option key={session.session_id} value={session.session_id}>
              <FaFolderOpen style={{ marginRight: 6 }} />{session.session_id}
            </option>
          ))}
        </Dropdown>
        <Dropdown defaultValue="All">
          <option value="All"><FaFilter style={{ marginRight: 6 }} />All</option>
          <option value="Annotated"><FaFilter style={{ marginRight: 6 }} />Annotated</option>
          <option value="Partially Annotated"><FaFilter style={{ marginRight: 6 }} />Partially Annotated</option>
          <option value="Not Annotated"><FaFilter style={{ marginRight: 6 }} />Not Annotated</option>
        </Dropdown>
      </LeftGroup>
      <RightGroup>
        <Button><Icon><MdDoneAll /></Icon>Apply All</Button>
        <Button><Icon><FaDatabase /></Icon>Inject to DB</Button>
        <Button><Icon><FaCheckCircle /></Icon>Validate</Button>
        <Button><Icon><FaSearch /></Icon>Review</Button>
        <Button><Icon><FaMemory /></Icon>Memory Analysis</Button>
      </RightGroup>
    </Row>
  </NavBar>
);

export default TopNavBar;
