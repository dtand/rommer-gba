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
import { FaDatabase, FaCheckCircle, FaSearch, FaMemory } from 'react-icons/fa';
import { MdDoneAll, MdTimeline } from 'react-icons/md';
import { FaChevronDown, FaChevronUp } from 'react-icons/fa';
import { useSessionContext } from '../../contexts/SessionContext';
import { CustomDropdown } from '../CustomDropdown/CustomDropdown';
import { FrameContextFilter } from '../../api/frameContexts';
import { useFrameDataContext } from '../../contexts/FrameDataContext';
import CustomRangeInput from '../CustomRangeInput/CustomRangeInput';

const filterOptions = [
  'All',
  'Annotated',
  'Partially Annotated',
  'Not Annotated'
];

const TopNavBar: React.FC = () => {
  const { session, setSession, progress } = useSessionContext();
  const { setFilter, setCurrentStartId, resetState, setEndRangeValue, fetchFrames, endRangeValue } = useFrameDataContext();
  const [filter, setFilterLocal] = useState('All');
  const [sessions, setSessions] = useState<any[]>([]);
  const [showCustomRange, setShowCustomRange] = useState(false);
  const [customStart, setCustomStart] = useState<string>(() => '1');
  const [customEnd, setCustomEnd] = useState<string>(() => session?.metadata?.total_frame_sets ? String(session.metadata.total_frame_sets) : '');
  const [appliedStart, setAppliedStart] = useState<string>('1');
  const [appliedEnd, setAppliedEnd] = useState<string>(() => session?.metadata?.total_frame_sets ? String(session.metadata.total_frame_sets) : '');

  useEffect(() => {
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

  const filterMap: Record<string, FrameContextFilter> = {
    'All': 'ALL',
    'Annotated': 'ANNOTATED',
    'Partially Annotated': 'PARTIALLY_ANNOTATED',
    'Not Annotated': 'NOT_ANNOTATED',
  };

  useEffect(() => {
    setFilter(filterMap[filter]);
  }, [filter]);

  const handleCustomRange = () => {
    setShowCustomRange(true);
  };

  const handleCustomRangeSubmit = () => {
    setShowCustomRange(false);
    setCurrentStartId(customStart);
    if (!isNaN(Number(customEnd))) {
      setEndRangeValue(Number(customEnd));
    }
    setAppliedStart(customStart);
    setAppliedEnd(customEnd);
    resetState();
    // Set filter to 'ALL' for custom range mode
    setFilterLocal('All');
    // Fetch frames for the custom range
    fetchFrames(customStart, false);
  };

  useEffect(() => {
    // Update default end value if session changes
    setCustomEnd(session?.metadata?.total_frame_sets ? String(session.metadata.total_frame_sets) : '');
  }, [session?.metadata?.total_frame_sets]);

  // Compute range label for Range button
  const isCustomRange = appliedStart !== '1' || (appliedEnd && appliedEnd !== String(totalFrames));
  const rangeLabel = isCustomRange ? `${appliedStart}–${appliedEnd}` : 'All Frames';

  const handleResetRange = () => {
    setCustomStart('1');
    setCustomEnd(String(totalFrames));
    setAppliedStart('1');
    setAppliedEnd(String(totalFrames));
    setCurrentStartId('1');
    setEndRangeValue(null);
    resetState();
    setFilterLocal('All');
    fetchFrames('1', false);
  };

  return (
    <NavBar>
      <Row>
        <LeftGroup>
          <LogoImage src="/rommer-gba.png" alt="Logo" />
          <CustomDropdown
            label="Sessions"
            options={sessions.map((s: any) => s.session_id)}
            value={selectedSession}
            width={"400px"}
            onChange={id => {
              const found = sessions.find((s: any) => s.session_id === id);
              setSession(found ? { id: found.session_id, metadata: found.metadata } : null);
            }}
          />
          <CustomDropdown
            label="Filters"
            options={filterOptions}
            value={filter}
            width={"200px"}
            onChange={val => {
              setFilterLocal(val);
            }}
          />
        </LeftGroup>
        <RightGroup>
          <div style={{ position: 'relative', display: 'inline-block', paddingLeft: 42 }}>
            <Button
              style={{ marginLeft: 8 }}
              onClick={() => setShowCustomRange(show => !show)}
            >
              <Icon><MdTimeline /></Icon>
              {rangeLabel}
              <span style={{ marginLeft: 6, fontSize: '1.1em', verticalAlign: 'middle' }}>
                {showCustomRange ? <FaChevronUp /> : <FaChevronDown />}
              </span>
            </Button>
            {showCustomRange && (
              <CustomRangeInput
                start={customStart}
                end={customEnd}
                setStart={setCustomStart}
                setEnd={setCustomEnd}
                onApply={handleCustomRangeSubmit}
                onCancel={() => setShowCustomRange(false)}
                onReset={handleResetRange}
                isCustomRange={!!isCustomRange}
              />
            )}
          </div>
          <Button><Icon><MdDoneAll /></Icon>Apply All</Button>
          <Button><Icon><FaDatabase /></Icon>Inject to DB</Button>
          <Button><Icon><FaCheckCircle /></Icon>Validate</Button>
          <Button><Icon><FaSearch /></Icon>Review</Button>
        </RightGroup>
        <RightGroup style={{ marginLeft: 'auto' }}>
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
