import React from 'react';
import {
  AllTagsContainer,
  AllTagsHeader,
  AllTagsList,
  TagRow,
  CloseButton,
  SearchBar
} from './AllTagsPanel.styled';

interface AllTagsPanelProps {
  tags: string[];
  onSelect: (tag: string) => void;
  onClose: () => void;
}

const AllTagsPanel: React.FC<AllTagsPanelProps> = ({ tags, onSelect, onClose }) => {
  const [search, setSearch] = React.useState('');
  const filteredTags = search
    ? tags.filter(tag => tag.toLowerCase().includes(search.toLowerCase()))
    : tags;

  return (
    <AllTagsContainer>
      <CloseButton onClick={onClose} aria-label="Close">×</CloseButton>
      <AllTagsHeader>All Tags</AllTagsHeader>
      <SearchBar
        type="text"
        placeholder="Search tags..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        autoFocus
      />
      <AllTagsList>
        {filteredTags.map(tag => (
          <TagRow key={tag} onClick={() => onSelect(tag)}>
            {tag}
          </TagRow>
        ))}
      </AllTagsList>
    </AllTagsContainer>
  );
};

export default AllTagsPanel;
