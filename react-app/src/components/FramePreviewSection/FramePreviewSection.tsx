import React from 'react';
import { FrameImagePreview } from '../AnnotationsModal/AnnotationsModal.styled';
import { FaGamepad } from 'react-icons/fa';
import { FramePreviewSectionContainer, FramePreviewButtonsRow, FramePreviewNoButtons, TagList, TagItem } from './FramePreviewSection.styled';

interface FramePreviewSectionProps {
  activeFrameImage: string | null;
  activeFrame: any;
}

const FramePreviewSection: React.FC<FramePreviewSectionProps> = ({ activeFrameImage, activeFrame }) => (
  <FramePreviewSectionContainer>
    {activeFrameImage ? (
      <FrameImagePreview src={activeFrameImage} alt="Active Frame" />
    ) : (
      <FrameImagePreview src="/placeholder.png" alt="No Image" />
    )}
    <FramePreviewButtonsRow>
      <FaGamepad size={22} style={{ color: '#888' }} />
      {Array.isArray(activeFrame?.buttons) && activeFrame.buttons.filter((b: string) => b && b !== 'None').length > 0 ? (
        <TagList style={{ justifyContent: 'flex-start', alignItems: 'center', flexWrap: 'nowrap', gap: '8px', marginBottom: 0 }}>
          {activeFrame.buttons.filter((b: string) => b && b !== 'None').map((btn: string, idx: number) => (
            <TagItem key={idx}>{btn}</TagItem>
          ))}
        </TagList>
      ) : (
        <FramePreviewNoButtons>No buttons for selections</FramePreviewNoButtons>
      )}
    </FramePreviewButtonsRow>
  </FramePreviewSectionContainer>
);

export default FramePreviewSection;
