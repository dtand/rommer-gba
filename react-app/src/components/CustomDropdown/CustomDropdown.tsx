import React from 'react';
import {
  DropdownWrapper,
  DropdownButton,
  DropdownList,
  DropdownHeader,
  DropdownItem,
  DropdownCaret
} from './CustomDropdown.styled';

export interface CustomDropdownProps {
  label: string;
  options: string[];
  value: string;
  onChange: (value: string) => void;
}

export const CustomDropdown: React.FC<CustomDropdownProps> = ({ label, options, value, onChange }) => {
  const [open, setOpen] = React.useState(false);

  const handleSelect = (option: string) => {
    onChange(option);
    setOpen(false);
  };

  return (
    <DropdownWrapper>
      <DropdownButton onClick={() => setOpen(o => !o)}>
        <span>{value || label}</span>
        <DropdownCaret>{open ? '\u25B2' : '\u25BC'}</DropdownCaret>
      </DropdownButton>
      {open && (
        <DropdownList>
          <DropdownHeader>{label}</DropdownHeader>
          {options.map(opt => (
            <DropdownItem key={opt} onClick={() => handleSelect(opt)}>
              {opt}
            </DropdownItem>
          ))}
        </DropdownList>
      )}
    </DropdownWrapper>
  );
};

export interface CustomDropdownWithAddNewProps extends CustomDropdownProps {
  onAddNew: (newValue: string) => void;
}

export const CustomDropdownWithAddNew: React.FC<CustomDropdownWithAddNewProps> = ({ label, options, value, onChange, onAddNew }) => {
  const [open, setOpen] = React.useState(false);
  const [addingNew, setAddingNew] = React.useState(false);
  const [newValue, setNewValue] = React.useState('');

  const handleSelect = (option: string) => {
    if (option === 'Add New +') {
      setAddingNew(true);
      return;
    }
    onChange(option);
    setOpen(false);
  };

  const handleAddNew = () => {
    if (newValue.trim()) {
      onAddNew(newValue.trim());
      onChange(newValue.trim());
      setNewValue('');
      setAddingNew(false);
      setOpen(false);
    }
  };

  return (
    <DropdownWrapper>
      <DropdownButton onClick={() => setOpen(o => !o)}>
        <span>{value || label}</span>
        <DropdownCaret>{open ? '\u25B2' : '\u25BC'}</DropdownCaret>
      </DropdownButton>
      {open && (
        <>
          <DropdownList>
            <DropdownHeader>{label}</DropdownHeader>
            {options.map(opt => (
              <DropdownItem key={opt} onClick={() => handleSelect(opt)}>
                {opt}
              </DropdownItem>
            ))}
            <DropdownItem key="add-new" onClick={() => handleSelect('Add New +')} style={{ color: '#007bff', fontWeight: 500 }}>
              Add New +
            </DropdownItem>
          </DropdownList>
          {addingNew && (
            <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
              <input
                type="text"
                value={newValue}
                onChange={e => setNewValue(e.target.value)}
                placeholder={`Add new ${label.toLowerCase()}`}
                style={{ flex: 1 }}
              />
              <button onClick={handleAddNew} style={{ padding: '6px 12px', borderRadius: 4, background: '#eee', border: '1px solid #ccc', cursor: 'pointer' }}>
                Add
              </button>
            </div>
          )}
        </>
      )}
    </DropdownWrapper>
  );
};
