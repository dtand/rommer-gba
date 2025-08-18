import React from 'react';
import {
  RangeInputContainer,
  RangeInputGrid,
  RangeLabel,
  RangeInput,
  RangeButtonRow,
  RangeButton
} from './CustomRangeInput.styled';

interface CustomRangeInputProps {
  start: string;
  end: string;
  setStart: (val: string) => void;
  setEnd: (val: string) => void;
  onApply: () => void;
  onCancel: () => void;
  onReset?: () => void;
  isCustomRange?: boolean;
}

const CustomRangeInput: React.FC<CustomRangeInputProps> = ({ start, end, setStart, setEnd, onApply, onCancel, onReset, isCustomRange }) => (
  <RangeInputContainer>
    <RangeInputGrid>
      <RangeLabel htmlFor="start-frame">Start Frame:</RangeLabel>
      <RangeInput id="start-frame" type="number" value={start} onChange={e => setStart(e.target.value)} />
      <RangeLabel htmlFor="end-frame">End Frame:</RangeLabel>
      <RangeInput id="end-frame" type="number" value={end} onChange={e => setEnd(e.target.value)} />
    </RangeInputGrid>
    <RangeButtonRow>
      <RangeButton onClick={onApply}>Apply</RangeButton>
      <RangeButton as="button" onClick={onCancel}>Cancel</RangeButton>
      {isCustomRange && onReset && (
        <RangeButton as="button" onClick={onReset}>Reset</RangeButton>
      )}
    </RangeButtonRow>
  </RangeInputContainer>
);

export default CustomRangeInput;
