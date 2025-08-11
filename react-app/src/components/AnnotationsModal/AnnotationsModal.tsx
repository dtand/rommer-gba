import React, { useState } from 'react';
import {
  ModalOverlay,
  ModalContent,
  CloseButton,
  ModalTitle,
  ModalDivider,
  ModalSection,
  ModalCol,
  FrameImagePreview,
  ModalButtonRow,
  TagList,
  TagItem,
  QuickSelectTags,
  QuickTagButton,
  ModalTagsRow
} from './AnnotationsModal.styled';
import { CustomDropdownWithAddNew } from '../CustomDropdown/CustomDropdown';
import { FaGamepad, FaRegImage } from 'react-icons/fa';

interface AnnotationsModalProps {
  isOpen: boolean;
  onClose: () => void;
  annotations: any[];
  modalFrameIds: number[];
  activeFrame: any;
  activeFrameImage: string | null;
  contextFields: any;
  sceneFields: any;
  actionsAggregate: any;
}

const BUTTONS = ['A', 'B', 'L', 'R', 'Start', 'Select', 'Up', 'Down', 'Left', 'Right'];
const QUICK_TAGS = ['Important', 'Bug', 'Review', 'Gameplay', 'Story'];
const ACTIONS = ['Jump', 'Attack', 'Defend', 'Interact'];
const INTENTS = ['Explore', 'Progress', 'Test'];
const OUTCOMES = ['Success', 'Failure', 'Neutral'];
const CONTEXTS = ['Battle', 'Menu', 'Overworld'];
const SCENES = ['Intro', 'Boss', 'Puzzle'];

const getInitialValues = (activeFrame: any) => {
  let source = activeFrame?.annotations && Object.keys(activeFrame.annotations).length > 0
    ? activeFrame.annotations
    : activeFrame?.cnn_annotations || {};
  return {
    context: source.context?.prediction || source.context || '',
    scene: source.scene?.prediction || source.scene || '',
    tags: Array.isArray(source.tags) ? source.tags : [],
    action: source.action?.prediction || source.action || '',
  };
};

const AnnotationsModal: React.FC<AnnotationsModalProps> = ({ isOpen, onClose, annotations, modalFrameIds, activeFrame, activeFrameImage, contextFields, sceneFields, actionsAggregate }) => {
  const initial = getInitialValues(activeFrame);
  const [tags, setTags] = useState<string[]>(initial.tags);
  const [tagInput, setTagInput] = useState('');
  const [action, setAction] = useState(initial.action);
  const [intent, setIntent] = useState('');
  const [outcome, setOutcome] = useState('');
  const [context, setContext] = useState(initial.context);
  const [scene, setScene] = useState(initial.scene);

  // Local state for dropdown options
  const [contextOptions, setContextOptions] = useState<string[]>(contextFields?.fields || []);
  const [sceneOptions, setSceneOptions] = useState<string[]>(sceneFields?.fields || []);
  const [actionOptions, setActionOptions] = useState<string[]>(actionsAggregate?.actions || []);
  const [intentOptions, setIntentOptions] = useState<string[]>(INTENTS);
  const [outcomeOptions, setOutcomeOptions] = useState<string[]>(OUTCOMES);

  React.useEffect(() => {
    setTags(initial.tags);
    setAction(initial.action);
    setContext(initial.context);
    setScene(initial.scene);
    setContextOptions(contextFields?.fields || []);
    setSceneOptions(sceneFields?.fields || []);
    setActionOptions(actionsAggregate?.actions || []);
  }, [activeFrame, contextFields, sceneFields, actionsAggregate]);

  if (!isOpen) return null;

  // Handle adding a tag

  const handleAddTag = () => {
    if (tagInput && !tags.includes(tagInput)) {
      setTags([...tags, tagInput]);
      setTagInput('');
    }
  };

  const handleQuickTag = (tag: string) => {
    if (!tags.includes(tag)) setTags([...tags, tag]);
  };

  return (
    <ModalOverlay>
      <ModalContent>
        <CloseButton onClick={onClose}>×</CloseButton>
        <ModalTitle>Annotate Selected Frames</ModalTitle>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center', marginBottom: '10px', maxWidth: '100%', overflowX: 'auto' }}>
          <FaRegImage size={18} style={{ color: '#888', marginRight: '2px' }} />
          {Array.isArray(modalFrameIds) && modalFrameIds.length > 0 && (
            <>
              {modalFrameIds.slice(0, 10).map((frameId, idx) => (
                <span key={frameId || idx} style={{ fontSize: '0.85em', background: '#e0e0e0', color: '#555', borderRadius: '10px', padding: '2px 10px', fontWeight: 500 }}>
                  {frameId}
                </span>
              ))}
              {modalFrameIds.length > 12 && (
                <span style={{ fontSize: '0.85em', background: '#e0e0e0', color: '#555', borderRadius: '10px', padding: '2px 10px', fontWeight: 500 }}>
                  +{modalFrameIds.length - 10} more
                </span>
              )}
            </>
          )}
        </div>
        <ModalDivider />
        {/* Section 1 */}
        <ModalSection>
          <div style={{ display: 'grid', gridTemplateColumns: '440px 1fr', gap: '56px', alignItems: 'stretch', minHeight: '520px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              {activeFrameImage ? (
                <FrameImagePreview src={activeFrameImage} alt="Active Frame" />
              ) : (
                <FrameImagePreview src="/placeholder.png" alt="No Image" />
              )}
              <div style={{ marginTop: '18px', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                <FaGamepad size={22} style={{ color: '#888' }} />
                {Array.isArray(activeFrame?.buttons) && activeFrame.buttons.filter((b: string) => b && b !== 'None').length > 0 ? (
                  <TagList style={{ justifyContent: 'flex-start', alignItems: 'center', flexWrap: 'nowrap', gap: '8px', marginBottom: 0 }}>
                    {activeFrame.buttons.filter((b: string) => b && b !== 'None').map((btn: string, idx: number) => (
                      <TagItem key={idx}>{btn}</TagItem>
                    ))}
                  </TagList>
                ) : (
                  <span style={{ color: '#aaa', fontSize: '1rem' }}>No buttons for selections</span>
                )}
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', justifyContent: 'flex-start', width: '100%', height: '100%', marginTop: '12px' }}>
              {/* All dropdowns and inputs stacked here, now vertically centered */}
              <div>
                <label><strong>Context:</strong></label>
                <CustomDropdownWithAddNew
                  label="Select context"
                  options={[...contextOptions]}
                  value={context}
                  onChange={setContext}
                  onAddNew={newVal => setContextOptions(prev => [...prev, newVal])}
                />
              </div>
              <div>
                <label><strong>Scene:</strong></label>
                <CustomDropdownWithAddNew
                  label="Select scene"
                  options={[...sceneOptions]}
                  value={scene}
                  onChange={setScene}
                  onAddNew={newVal => setSceneOptions(prev => [...prev, newVal])}
                />
              </div>
              <div>
                <label><strong>Action:</strong></label>
                <CustomDropdownWithAddNew
                  label="Select action"
                  options={[...actionOptions]}
                  value={action}
                  onChange={setAction}
                  onAddNew={newVal => setActionOptions(prev => [...prev, newVal])}
                />
              </div>
              <div>
                <label><strong>Intent:</strong></label>
                <CustomDropdownWithAddNew
                  label="Select intent"
                  options={[...intentOptions]}
                  value={intent}
                  onChange={setIntent}
                  onAddNew={newVal => setIntentOptions(prev => [...prev, newVal])}
                />
              </div>
              <div>
                <label><strong>Outcome:</strong></label>
                <CustomDropdownWithAddNew
                  label="Select outcome"
                  options={[...outcomeOptions]}
                  value={outcome}
                  onChange={setOutcome}
                  onAddNew={newVal => setOutcomeOptions(prev => [...prev, newVal])}
                />
              </div>
            </div>
          </div>
        </ModalSection>
        <ModalTagsRow>
          <TagList style={{ justifyContent: 'flex-start', width: '100%' }}>
            {tags.map(tag => <TagItem key={tag}>{tag}</TagItem>)}
          </TagList>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-start', width: '100%' }}>
            <input
              type="text"
              value={tagInput}
              onChange={e => {
                const val = e.target.value;
                if (/^[a-zA-Z0-9_]*$/.test(val)) {
                  setTagInput(val);
                }
              }}
              placeholder="Add tag (alphanumeric & underscores only)"
              style={{ textAlign: 'left', width: '40%', minWidth: '180px', maxWidth: '340px', padding: '10px 14px', fontSize: '1rem', border: '2px solid #d3d3d3', borderRadius: '4px' }}
            />
            <QuickTagButton style={{ marginLeft: 0 }} onClick={handleAddTag}>Add Tag+</QuickTagButton>
          </div>
          <QuickSelectTags style={{ justifyContent: 'flex-start', width: '100%' }}>
            {QUICK_TAGS.map(tag => (
              <QuickTagButton key={tag} onClick={() => handleQuickTag(tag)}>{tag}</QuickTagButton>
            ))}
          </QuickSelectTags>
        </ModalTagsRow>
        <ModalDivider />
        <ModalButtonRow>
          <QuickTagButton>Mark as complete</QuickTagButton>
          <QuickTagButton>Save</QuickTagButton>
        </ModalButtonRow>
      </ModalContent>
    </ModalOverlay>
  );
};

export default AnnotationsModal;
