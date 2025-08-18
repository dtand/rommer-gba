import React from 'react';
import {
  TagListStyled,
  TagItemStyled,
  TagRemoveIcon,
  TagInputRow,
  TagInputBox,
  QuickSelectTagsStyled,
  QuickSelectRow,
  QuickTagButton,
  TagActionButtonsRow
} from './TagInputSection.styled';
import { TagActionButton, ModalTagsRow } from '../AnnotationsModal/AnnotationsModal.styled';
import { useSessionContext } from '../../contexts/SessionContext';
import { useFrameDataContext } from '../../contexts/FrameDataContext';

interface TagInputSectionProps {
  tags: string[];
  setTags: (tags: string[]) => void;
  tagInput: string;
  setTagInput: (val: string) => void;
  quickSelectTags: string[];
  handleAddTag: () => void;
  handleQuickTag: (tag: string) => void;
  showAllTags: boolean;
  setShowAllTags: (show: boolean) => void;
}

const TagInputSection: React.FC<TagInputSectionProps> = ({
  tags,
  setTags,
  tagInput,
  setTagInput,
  quickSelectTags,
  handleAddTag,
  handleQuickTag,
  showAllTags,
  setShowAllTags,
}) => {
  const { previousAnnotation } = useSessionContext();
  const { frameContexts } = useFrameDataContext();

  let prevTags: string[] = [];
  if (Array.isArray(previousAnnotation?.tags) && previousAnnotation.tags.length > 0) {
    prevTags = previousAnnotation.tags;
  } else {
    for (let i = frameContexts.length - 1; i >= 0; i--) {
      const ctx = frameContexts[i];
      if (Array.isArray(ctx?.annotations?.tags) && ctx.annotations.tags.length > 0) {
        prevTags = ctx.annotations.tags;
        break;
      }
    }
  }

  const handleAddLast = () => {
    if (prevTags.length > 0) {
      setTags([...new Set([...tags, ...prevTags])]);
    }
  };

  // Compute quick select tags: prevTags (up to 4, unique) first, then the rest (excluding duplicates)
  const uniquePrevTags = Array.from(new Set(prevTags)).slice(0, 4);
  const remainingQuickTags = quickSelectTags.filter(tag => !uniquePrevTags.includes(tag));
  const combinedQuickSelect = [...uniquePrevTags, ...remainingQuickTags];

  return (
    <ModalTagsRow>
      <TagInputRow>
        <TagInputBox
          type="text"
          value={tagInput}
          onChange={e => {
            const val = e.target.value;
            if (/^[a-zA-Z0-9_]*$/.test(val)) {
              setTagInput(val);
            }
          }}
          placeholder="Add tag (alphanumeric & underscores only)"
        />
        <TagActionButtonsRow>
          <TagActionButton style={{ marginLeft: 0 }} onClick={handleAddTag}>Add Tag+</TagActionButton>
          <TagActionButton style={{ marginLeft: 0 }} onClick={handleAddLast} disabled={prevTags.length === 0}>Add Last+</TagActionButton>
          <TagActionButton style={{ marginLeft: 0 }} onClick={() => setShowAllTags(true)}>All Tags</TagActionButton>
          <TagActionButton style={{ marginLeft: 0 }} onClick={() => setTags([])}>Clear</TagActionButton>
        </TagActionButtonsRow>
      </TagInputRow>
      <TagListStyled>
        {tags.map(tag => (
          <TagItemStyled
            key={tag}
            title="Remove tag"
            onClick={() => setTags(tags.filter(t => t !== tag))}
          >
            {tag} <TagRemoveIcon>&times;</TagRemoveIcon>
          </TagItemStyled>
        ))}
      </TagListStyled>
      <QuickSelectTagsStyled>
        {Array.from({ length: 2 }).map((_, rowIdx) => (
          <QuickSelectRow key={rowIdx}>
            {combinedQuickSelect.slice(rowIdx * 8, rowIdx * 8 + 8).map(tag => (
              <QuickTagButton
                key={tag}
                onClick={() => handleQuickTag(tag)}
                className={uniquePrevTags.includes(tag) ? 'prev-annotation-match' : ''}
              >
                {tag}
              </QuickTagButton>
            ))}
          </QuickSelectRow>
        ))}
      </QuickSelectTagsStyled>
    </ModalTagsRow>
  );
};

export default TagInputSection;
