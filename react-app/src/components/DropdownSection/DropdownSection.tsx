import React from 'react';
import { CustomDropdown } from '../CustomDropdown/CustomDropdown';
import { DropdownSectionContainer } from './DropdownSection.styled';

interface DropdownSectionProps {
  context: string;
  setContext: (val: string) => void;
  contextOptions: string[];
  setContextOptions: (opts: string[]) => void;
  scene: string;
  setScene: (val: string) => void;
  sceneOptions: string[];
  setSceneOptions: (opts: string[]) => void;
  action: string;
  setAction: (val: string) => void;
  actionOptions: string[];
  setActionOptions: (opts: string[]) => void;
  intent: string;
  setIntent: (val: string) => void;
  intentOptions: string[];
  setIntentOptions: (opts: string[]) => void;
  outcome: string;
  setOutcome: (val: string) => void;
  outcomeOptions: string[];
  setOutcomeOptions: (opts: string[]) => void;
}

const DropdownSection: React.FC<DropdownSectionProps> = ({
  context, setContext, contextOptions, setContextOptions,
  scene, setScene, sceneOptions, setSceneOptions,
  action, setAction, actionOptions, setActionOptions,
  intent, setIntent, intentOptions, setIntentOptions,
  outcome, setOutcome, outcomeOptions, setOutcomeOptions,
}) => (
  <DropdownSectionContainer>
    <div>
      <label><strong>Context:</strong></label>
      <CustomDropdown
        label="Select context"
        options={contextOptions}
        value={context}
        onChange={setContext}
        onAddNew={newVal => setContextOptions([...contextOptions, newVal])}
        width={"400px"}
      />
    </div>
    <div>
      <label><strong>Scene:</strong></label>
      <CustomDropdown
        label="Select scene"
        options={sceneOptions}
        value={scene}
        onChange={setScene}
        onAddNew={newVal => setSceneOptions([...sceneOptions, newVal])}
        width={"400px"}
      />
    </div>
    <hr style={{ margin: '16px 0', border: 0, borderTop: '1px solid #e0e0e0' }} />
    <div>
      <label><strong>Optional: Action ➡️ Outcome ➡️ Intent</strong></label>
      <div style={{ maxWidth: 340, marginBottom: 8, marginTop: 8 }}>
        <CustomDropdown
          label="Select action"
          options={actionOptions}
          value={action}
          onChange={val => {
            setAction(val);
            setOutcome('');
            setIntent('');
          }}
          onAddNew={newVal => setActionOptions([...actionOptions, newVal])}
          allowNone
          width={"400px"}
        />
      </div>
      <div style={{ maxWidth: 340, marginBottom: 8 }}>
        <CustomDropdown
          label="Select outcome"
          options={outcomeOptions}
          value={outcome}
          onChange={val => {
            setOutcome(val);
            setIntent('');
          }}
          onAddNew={newVal => setOutcomeOptions([...outcomeOptions, newVal])}
          disabled={!action}
          width={"400px"}
        />
      </div>
      <div style={{ maxWidth: 340 }}>
        <CustomDropdown
          label="Select intent"
          options={intentOptions}
          value={intent}
          onChange={setIntent}
          onAddNew={newVal => setIntentOptions([...intentOptions, newVal])}
          disabled={!outcome}
          width={"400px"}
        />
      </div>
      <div style={{ fontSize: '0.92em', color: '#888', marginTop: 4 }}>
        If you select Action, you must also select Outcome, then Intent.
      </div>
    </div>
  </DropdownSectionContainer>
);

export default DropdownSection;
