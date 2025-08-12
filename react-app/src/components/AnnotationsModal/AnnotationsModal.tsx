import React, { useState } from 'react';
import {
  ModalOverlay,
  ModalContent,
  CloseButton,
  ModalTitle,
  ModalDivider,
  ModalSection,
  FrameImagePreview,
  ModalButtonRow,
  TagList,
  TagItem,
  QuickSelectTags,
  QuickTagButton,
  ModalTagsRow,
  MarkCompleteButton,
  SaveButton
} from './AnnotationsModal.styled';
import { CustomDropdownWithAddNew } from '../CustomDropdown/CustomDropdown';
import { FaGamepad, FaRegImage } from 'react-icons/fa';
import FrameIdListing from '../FrameIdListing/FrameIdListing';
import { useSessionContext } from '../../contexts/SessionContext';
import { useAnnotationContext } from '../../contexts/AnnotationContext';

const getInitialValues = (activeFrame: any) => {
  let source = activeFrame?.annotations && Object.keys(activeFrame.annotations).length > 0
    ? activeFrame.annotations
    : activeFrame?.cnn_annotations || {};
  return {
    context: source.context?.prediction || source.context || '',
    scene: source.scene?.prediction || source.scene || '',
    tags: Array.isArray(source.tags) ? source.tags : [],
    action: source.action_type?.prediction || source.action_type || '',
    intent: source.intent?.prediction || source.intent || '',
    outcome: source.outcome?.prediction || source.outcome || '',
  };
};

const AnnotationsModal: React.FC<{ isOpen: boolean; onClose: () => void; }> = ({ isOpen, onClose }) => {
  const { session } = useSessionContext();
  const {
    selectedFrameIds,
    activeFrame,
    activeFrameImage,
    selectedFrameContexts,
    setFrameContexts,
    setSelectedIndices,
    setSelectedFrameIds
  } = useAnnotationContext();
  // Get annotationFields from session context
  const { annotationFields } = useSessionContext();
  const initial = getInitialValues(activeFrame);
  const [tags, setTags] = useState<string[]>(initial.tags);
  const [tagInput, setTagInput] = useState('');
  const [action, setAction] = useState(initial.action);
  const [intent, setIntent] = useState('');
  const [outcome, setOutcome] = useState('');
  const [context, setContext] = useState(initial.context);
  const [scene, setScene] = useState(initial.scene);
  const [notification, setNotification] = useState<string | null>(null);

  // Local state for dropdown options
  const [contextOptions, setContextOptions] = useState<string[]>(annotationFields?.contexts || []);
  const [sceneOptions, setSceneOptions] = useState<string[]>(annotationFields?.scenes || []);
  const [actionOptions, setActionOptions] = useState<string[]>(annotationFields?.actions || []);
  const [intentOptions, setIntentOptions] = useState<string[]>(annotationFields?.intents || []);
  const [outcomeOptions, setOutcomeOptions] = useState<string[]>(annotationFields?.outcomes || []);
  const [tagsOptions, setTagsOptions] = useState<string[]>(annotationFields?.tags || []);

  React.useEffect(() => {
    setTags(initial.tags);
    setAction(initial.action);
    setContext(initial.context);
    setScene(initial.scene);
    setContextOptions(annotationFields?.contexts || []);
    setSceneOptions(annotationFields?.scenes || []);
    setActionOptions(annotationFields?.actions || []);
    setIntentOptions(annotationFields?.intents || []);
    setOutcomeOptions(annotationFields?.outcomes || []);
    setTagsOptions(annotationFields?.tags || []);
  }, [activeFrame, annotationFields]);

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

  const handleMarkComplete = async () => {
    const annotation = {
      context,
      scene,
      tags,
      action,
      intent,
      outcome,
      complete: true
    };
    const payload = {
      frames: selectedFrameIds,
      annotation
    };
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/annotate/${session?.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (response.ok) {
        setNotification('Frames marked complete!');
        setTimeout(() => setNotification(null), 2500);
        // Directly update annotation context here
        setFrameContexts((prev: any[]) => prev.map((ctx: any, idx: number) =>
          selectedFrameIds.includes(idx + 1) ? { ...ctx, annotations: { ...ctx.annotations, complete: true } } : ctx
        ));
        setSelectedIndices([]);
        setSelectedFrameIds([]);
        setTimeout(() => onClose(), 1200);
      } else {
        setNotification('Failed to mark frames complete.');
        setTimeout(() => setNotification(null), 2500);
      }
    } catch (err) {
      setNotification('Error marking frames complete.');
      setTimeout(() => setNotification(null), 2500);
    }
  };

  return (
    <ModalOverlay>
      <ModalContent>
        <CloseButton onClick={onClose}>×</CloseButton>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', marginBottom: '10px', maxWidth: '100%', overflowX: 'auto' }}>
          <ModalTitle>Annotate Selected Frames</ModalTitle>
          <FrameIdListing modalFrameIds={selectedFrameIds} />
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
          <QuickSelectTags style={{ justifyContent: 'flex-start', width: '100%', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {Array.from({ length: 2 }).map((_, rowIdx) => (
              <div key={rowIdx} style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                {tagsOptions.slice(rowIdx * 8, rowIdx * 8 + 8).map(tag => (
                  <QuickTagButton key={tag} onClick={() => handleQuickTag(tag)}>{tag}</QuickTagButton>
                ))}
              </div>
            ))}
          </QuickSelectTags>
        </ModalTagsRow>
        <ModalDivider />
        <ModalButtonRow>
          <MarkCompleteButton onClick={handleMarkComplete}>Mark as complete</MarkCompleteButton>
          <SaveButton>Save</SaveButton>
        </ModalButtonRow>
        {notification && (
          <div style={{
            position: 'fixed',
            top: 32,
            right: 32,
            background: '#43e97b',
            color: '#fff',
            padding: '16px 32px',
            borderRadius: '12px',
            fontWeight: 600,
            fontSize: '1.1rem',
            boxShadow: '0 2px 12px #43e97b55',
            zIndex: 99999
          }}>
            {notification}
          </div>
        )}
      </ModalContent>
    </ModalOverlay>
  );
};

export default AnnotationsModal;
