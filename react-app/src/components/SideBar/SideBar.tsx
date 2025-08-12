import React from 'react';
import { Aside, MenuTitle, AnnotationContainer, TagPillContainer, TagPill, ActionList } from './SideBar.styled';
import { FaGamepad, FaRegImage, FaUser, FaRobot } from 'react-icons/fa';
import { useAnnotationContext } from '../../contexts/AnnotationContext';

const Divider = () => (
  <div style={{ width: '100%', height: '1px', background: '#e0e0e0', margin: '12px 0' }} />
);

const SideBar: React.FC = () => {
  const { activeFrame, activeFrameImage, activeFrameId } = useAnnotationContext();

  const frameIdText = activeFrameId != null && activeFrameId !== undefined ? `Frame: ${activeFrameId}` : 'No frame selected';
  const annotations = activeFrame?.annotations;
  const cnnAnnotations = activeFrame?.cnn_annotations;
  const framesInSet = activeFrame?.frames_in_set;
  const buttons = activeFrame?.buttons;

  const isAnnotations = annotations && Object.keys(annotations).length > 0;
  const isCNN = !isAnnotations && cnnAnnotations;

  let hasButtonPresses = false;
  let buttonPresses: string[] = [];
  if (Array.isArray(buttons)) {
    buttonPresses = buttons.filter(b => b && b !== 'None');
    hasButtonPresses = buttonPresses.length > 0;
  }

  // Get annotation values
  const annotationSource = isAnnotations ? annotations : (isCNN ? cnnAnnotations : {});
  const contextValue = annotationSource?.context?.prediction || annotationSource?.context || '';
  const sceneValue = annotationSource?.scene?.prediction || annotationSource?.scene || '';
  const tagsValue = Array.isArray(annotationSource?.tags) ? annotationSource.tags : [];
  const actionType = annotationSource?.action_type || '';
  const intent = annotationSource?.intent || '';
  const outcome = annotationSource?.outcome || '';

  if (!activeFrame) {
    return (
      <Aside>
        <MenuTitle style={{ textAlign: 'center', color: '#bbb', fontWeight: 500 }}>No frame selected</MenuTitle>
        <div style={{ width: '100%', height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f0f2f5', borderRadius: '8px', marginBottom: '16px' }}>
          <FaRegImage size={64} color="#ccc" />
        </div>
      </Aside>
    );
  }

  return (
    <Aside>
      <MenuTitle style={{ textAlign: 'center' }}>{frameIdText}</MenuTitle>
      {activeFrameImage && (
        <img src={activeFrameImage} alt="Active Frame" style={{ width: '100%', borderRadius: '8px', marginBottom: '16px' }} />
      )}
      {framesInSet && (
        <section style={{ marginBottom: '1rem' }}>
          <strong>Frames In Set</strong>
          <div>{Array.isArray(framesInSet) ? framesInSet.join(', ') : framesInSet}</div>
        </section>
      )}
      <section style={{ marginBottom: '1rem' }}>
        <strong>Buttons</strong>
        <TagPillContainer>
          {buttonPresses.length > 0 ? buttonPresses.map((btn, idx) => (
            <TagPill key={idx}>{btn}</TagPill>
          )) : <span style={{ color: '#888' }}>No buttons pressed</span>}
        </TagPillContainer>
        <Divider />
      </section>
      <section style={{ marginBottom: '1rem' }}>
        {isAnnotations && (
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
            <FaUser style={{ color: '#007bff', marginRight: 6 }} />
            <span style={{ fontWeight: 600, color: '#007bff' }}>Manual Annotation</span>
          </div>
        )}
        {isCNN && (
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
            <FaRobot style={{ color: '#28a745', marginRight: 6 }} />
            <span style={{ fontWeight: 600, color: '#28a745' }}>AI Annotation</span>
          </div>
        )}
        <ActionList>
          <div><strong>Context:</strong> {contextValue || <span style={{ color: '#888' }}>None</span>}</div>
          <div><strong>Scene:</strong> {sceneValue || <span style={{ color: '#888' }}>None</span>}</div>
        </ActionList>
        <ActionList>
          <div><strong>Action:</strong> {actionType || <span style={{ color: '#888' }}>None</span>}</div>
          <div><strong>Intent:</strong> {intent || <span style={{ color: '#888' }}>None</span>}</div>
          <div><strong>Outcome:</strong> {outcome || <span style={{ color: '#888' }}>None</span>}</div>
        </ActionList>
      </section>
      <section style={{ marginBottom: '1rem', marginTop: 'auto' }}>
        <div style={{ marginBottom: 4 }}><strong>Tags</strong></div>
        <TagPillContainer>
          {tagsValue.length > 0 ? tagsValue.map((tag: string, idx: number) => (
            <TagPill key={idx}>{tag}</TagPill>
          )) : <span style={{ color: '#888' }}>No tags</span>}
        </TagPillContainer>
      </section>
    </Aside>
  );
};

export default SideBar;
