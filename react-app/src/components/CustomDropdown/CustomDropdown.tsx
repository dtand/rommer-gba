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
  onAddNew?: (newValue: string) => void;
  disabled?: boolean;
  allowNone?: boolean;
  action?: React.ReactNode;
  handleAction?: () => void;
  width?: string;
}

export const CustomDropdown: React.FC<CustomDropdownProps> = ({
  label,
  options,
  value,
  onChange,
  onAddNew,
  disabled,
  allowNone,
  action,
  handleAction,
  width
}) => {
  const [open, setOpen] = React.useState(false);
  const [addingNew, setAddingNew] = React.useState(false);
  const [newValue, setNewValue] = React.useState('');
  const [filter, setFilter] = React.useState('');

  const filteredOptions = React.useMemo(() => {
    let opts = options;
    if (allowNone) opts = ['None', ...opts];
    if (!filter) return opts;
    return opts.filter(opt => opt.toLowerCase().includes(filter.toLowerCase()));
  }, [options, filter, allowNone]);

  const handleSelect = (option: string) => {
    if (option === 'Add New +' && onAddNew) {
      setAddingNew(true);
      return;
    }
    onChange(option === 'None' ? '' : option);
    setOpen(false);
    setFilter('');
    setAddingNew(false);
    setNewValue('');
  };

  const handleAddNew = () => {
    if (newValue.trim() && onAddNew) {
      onAddNew(newValue.trim());
      onChange(newValue.trim());
      setNewValue('');
      setAddingNew(false);
      setOpen(false);
      setFilter('');
    }
  };

  return (
    <DropdownWrapper width={width}>
      <DropdownButton width={width} onClick={() => !disabled && setOpen(o => !o)} disabled={disabled} style={disabled ? { opacity: 0.5, cursor: 'not-allowed' } : {}}>
        <span>{value || label}</span>
        <DropdownCaret>{open ? '\u25B2' : '\u25BC'}</DropdownCaret>
      </DropdownButton>
      {open && !disabled && (
        <>
          <DropdownList width={width}>
            <DropdownHeader>{label}</DropdownHeader>
            <div style={{ padding: '4px 8px' }}>
              <input
                type="text"
                value={filter}
                onChange={e => setFilter(e.target.value)}
                placeholder="Type to filter..."
                style={{ width: '100%', padding: '4px', fontSize: '1em', boxSizing: 'border-box' }}
                autoFocus
              />
            </div>
            {filteredOptions.map(opt => (
              <DropdownItem key={opt} onClick={() => handleSelect(opt)}>
                {opt}
              </DropdownItem>
            ))}
            {onAddNew && (
              <DropdownItem key="add-new" onClick={() => handleSelect('Add New +')} style={{ color: '#007bff', fontWeight: 500 }}>
                Add New +
              </DropdownItem>
            )}
            {action && handleAction && (
              <DropdownItem key="custom-action" onClick={handleAction} style={{ color: '#007bff', fontWeight: 500 }}>
                {action}
              </DropdownItem>
            )}
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
