import React, { useState } from 'react';
import {
  ModalOverlay,
  ModalContent,
  CloseButton,
  ModalTitle,
  ModalDivider,
  ModalSection,
  ModalButtonRow,
  MarkCompleteButton,
  SaveButton
} from './AnnotationsModal.styled';
import FrameIdListing from '../FrameIdListing/FrameIdListing';
import { useSessionContext } from '../../contexts/SessionContext';
import { getFrameDataById, useFrameDataContext } from '../../contexts/FrameDataContext';
import { useFrameSelection } from '../../contexts/FrameSelectionContext';
import FramesCompleteNotification from '../FramesCompleteNotification/FramesCompleteNotification';
import { useAnnotationFieldsCache } from '../../contexts/AnnotationFieldsCacheContext';
import TagInputSection from '../TagInputSection/TagInputSection';
import DropdownSection from '../DropdownSection/DropdownSection';
import FramePreviewSection from '../FramePreviewSection/FramePreviewSection';
import AllTagsPanel from '../AllTagsPanel/AllTagsPanel';
import { MdEditNote } from 'react-icons/md'; // annotation/pen on paper icon

const getInitialValues = (activeFrame: any) => {
  let source = activeFrame?.annotations && Object.keys(activeFrame.annotations).length > 0
    ? activeFrame.annotations
    : activeFrame?.cnn_annotations || {};
  return {
    context: source.context?.prediction || source.context || '',
    scene: source.scene?.prediction || source.scene || '',
    tags: Array.isArray(source.tags) ? source.tags : [],
    action: source.action?.prediction || source.action || '',
    intent: source.intent?.prediction || source.intent || '',
    outcome: source.outcome?.prediction || source.outcome || '',
  };
};

const AnnotationsModal: React.FC<{ isOpen: boolean; onClose: () => void; }> = ({ isOpen, onClose }) => {
  const { session, updateRecentFields, recentAnnotationFields, previousAnnotation, setPreviousAnnotation } = useSessionContext();
  const { getFields } = useAnnotationFieldsCache();
  const annotationFields = session?.metadata?.game_name ? getFields(session.metadata.game_name) : undefined;

  const { frameContexts, frameImages, setFrameContexts, updateFrameContexts } = useFrameDataContext();
  const { activeFrameId, selectedFrameIds } = useFrameSelection();
  
  const activeFrameData = getFrameDataById(frameContexts, frameImages, activeFrameId);
  const activeFrame = activeFrameData.context;
  const activeFrameImage = activeFrameData.image;
  
  const initial = getInitialValues(activeFrame);
  const [tags, setTags] = useState<string[]>(initial.tags);
  const [tagInput, setTagInput] = useState('');
  const [action, setAction] = useState(initial.action);
  const [intent, setIntent] = useState(initial.intent);
  const [outcome, setOutcome] = useState(initial.outcome);
  const [context, setContext] = useState(initial.context);
  const [scene, setScene] = useState(initial.scene);
  const [notification, setNotification] = useState<string | null>(null);
  const [contextOptions, setContextOptions] = useState<string[]>(annotationFields?.contexts || []);
  const [sceneOptions, setSceneOptions] = useState<string[]>(annotationFields?.scenes || []);
  const [actionOptions, setActionOptions] = useState<string[]>(annotationFields?.actions || []);
  const [intentOptions, setIntentOptions] = useState<string[]>(annotationFields?.intents || []);
  const [outcomeOptions, setOutcomeOptions] = useState<string[]>(annotationFields?.outcomes || []);
  const [tagsOptions, setTagsOptions] = useState<string[]>(annotationFields?.tags || []);
  const [showAllTags, setShowAllTags] = useState(false);

  React.useEffect(() => {
    setTags(initial.tags);
    setAction(initial.action);
    setContext(initial.context);
    setScene(initial.scene);
    setIntent(''); // Always clear intent on frame change
    setOutcome(''); // Always clear outcome on frame change
    setContextOptions(annotationFields?.contexts || []);
    setSceneOptions(annotationFields?.scenes || []);
    setActionOptions(annotationFields?.actions || []);
    setIntentOptions(annotationFields?.intents || []);
    setOutcomeOptions(annotationFields?.outcomes || []);
    setTagsOptions(annotationFields?.tags || []);
  }, [activeFrame, annotationFields]);

  // Compute quick select tags: first from recent, then from annotationFields (excluding recents)
  const maxQuickSelects = 16;
  const recentTags = recentAnnotationFields.tags || [];
  const annotationTags = annotationFields?.tags || [];
  const remainingTags = annotationTags.filter(tag => !recentTags.includes(tag));
  const quickSelectTags = [...recentTags, ...remainingTags].slice(0, maxQuickSelects);

  // Helper to exit modal immediately, but keep notification
  const [shouldRenderModal, setShouldRenderModal] = useState(true);
  const [completedFrameIds, setCompletedFrameIds] = useState<number[]>([]);
  const [showNotification, setShowNotification] = useState(false);

  const exitModal = () => {
    setShouldRenderModal(false);
    setShowNotification(true);
    setTimeout(() => {
      setNotification(null);
      setCompletedFrameIds([]);
      setShowNotification(false);
      onClose();
      setShouldRenderModal(true); // reset for next open
    }, 2500); // notification stays for 2.5s
  };

  const handleNotificationClose = () => {
    setShowNotification(false);
    setNotification(null);
    setCompletedFrameIds([]);
  };

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
    // If action is blank, do not send intent or outcome
    const annotation = {
      context,
      scene,
      tags,
      action,
      intent: action ? intent : undefined,
      outcome: action ? outcome : undefined,
      complete: true
    };
    setPreviousAnnotation(annotation);
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
        setCompletedFrameIds(selectedFrameIds.map(id => Number(id)));
        setFrameContexts((prev: any[]) => prev.map((ctx: any) =>
          selectedFrameIds.includes(ctx.frame_set_id) ? { ...ctx, annotations: { ...ctx.annotations, complete: true } } : ctx
        ));
        if (typeof updateFrameContexts === 'function') {
          updateFrameContexts(selectedFrameIds, annotation);
        }
        // Update recent fields
        if (context) updateRecentFields('contexts', context);
        if (scene) updateRecentFields('scenes', scene);
        tags.forEach(tag => updateRecentFields('tags', tag));
        exitModal();
      } else {
        setNotification('Failed to mark frames complete.');
        setTimeout(() => setNotification(null), 2500);
      }
    } catch (err) {
      setNotification('Error marking frames complete.');
      setTimeout(() => setNotification(null), 2500);
    }
  };

  const handleSave = () => {
    setNotification('Saved!');
    setCompletedFrameIds(selectedFrameIds.map(id => Number(id)));
    // Update recent fields
    if (context) updateRecentFields('contexts', context);
    if (scene) updateRecentFields('scenes', scene);
    tags.forEach(tag => updateRecentFields('tags', tag));
    exitModal();
  };

  if (!isOpen && !notification) return null;

  return (
    <>
      {shouldRenderModal && isOpen && (
        <ModalOverlay>
          <ModalContent>
            <CloseButton onClick={exitModal}>×</CloseButton>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', maxWidth: '100%', overflowX: 'auto' }}>
              <ModalTitle>
                <MdEditNote style={{ marginRight: 8, verticalAlign: 'middle', fontSize: 32 }} />
                Annotate Frame Set
              </ModalTitle>
              <FrameIdListing modalFrameIds={selectedFrameIds.map(id => Number(id))} />
            </div>
            <ModalDivider />
            {/* Section 1 */}
            <ModalSection>
              <div style={{ display: 'grid', gridTemplateColumns: '440px 1fr', gap: '56px', alignItems: 'stretch', minHeight: '520px' }}>
                <FramePreviewSection activeFrameImage={activeFrameImage || null} activeFrame={activeFrame} />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', justifyContent: 'flex-start', width: '100%', height: '100%', marginTop: '12px' }}>
                  <DropdownSection
                    context={context}
                    setContext={setContext}
                    contextOptions={contextOptions}
                    setContextOptions={setContextOptions}
                    scene={scene}
                    setScene={setScene}
                    sceneOptions={sceneOptions}
                    setSceneOptions={setSceneOptions}
                    action={action}
                    setAction={setAction}
                    actionOptions={actionOptions}
                    setActionOptions={setActionOptions}
                    intent={intent}
                    setIntent={setIntent}
                    intentOptions={intentOptions}
                    setIntentOptions={setIntentOptions}
                    outcome={outcome}
                    setOutcome={setOutcome}
                    outcomeOptions={outcomeOptions}
                    setOutcomeOptions={setOutcomeOptions}
                  />
                </div>
              </div>
            </ModalSection>
            <TagInputSection
              tags={tags}
              setTags={setTags}
              tagInput={tagInput}
              setTagInput={setTagInput}
              quickSelectTags={quickSelectTags}
              handleAddTag={handleAddTag}
              handleQuickTag={handleQuickTag}
              showAllTags={showAllTags}
              setShowAllTags={setShowAllTags}
            />
            {showAllTags && (
              <AllTagsPanel
                tags={annotationFields?.tags || []}
                onSelect={tag => {
                  if (!tags.includes(tag)) setTags([...tags, tag]);
                  // Do not close the panel on select
                }}
                onClose={() => setShowAllTags(false)}
              />
            )}
            <ModalDivider />
            <ModalButtonRow>
              <MarkCompleteButton onClick={handleMarkComplete}>Mark as complete</MarkCompleteButton>
              <SaveButton onClick={handleSave}>Save</SaveButton>
            </ModalButtonRow>
          </ModalContent>
        </ModalOverlay>
      )}
      {notification && showNotification && (
        <FramesCompleteNotification frameIds={completedFrameIds} onClose={handleNotificationClose} />
      )}
    </>
  );
};

export default AnnotationsModal;
