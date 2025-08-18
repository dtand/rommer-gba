// Frame Grid Annotator - Form Utilities
// Form handling, input history, and UI utilities

// Load dropdown data
function loadDropdownData() {
    // Populate dropdowns with correct property mapping
    populateDropdown('context', window.contextsLookup || []);
    // Scene is now a text input, not a dropdown
    // Use sorted arrays from actions-lookup.js
    populateDropdown('action', window.actionsLookup || []);
    populateDropdown('intent', window.intentsLookup || []);
    populateDropdown('outcome', window.outcomesLookup || []);
}

function populateDropdown(fieldName, options) {
    const select = document.getElementById(fieldName);
    if (!select) return;
    
    // Clear existing options except the first one (placeholder)
    const firstOption = select.firstElementChild;
    select.innerHTML = '';
    if (firstOption) {
        select.appendChild(firstOption);
    }
    
    // Add options from config
    options.forEach(option => {
        const optionElement = document.createElement('option');
        // Handle both string and object formats
        if (typeof option === 'string') {
            optionElement.value = option;
            // Transform snake_case to Title Case for display
            optionElement.textContent = option
                .replace(/_/g, ' ')
                .replace(/\b\w/g, c => c.toUpperCase());
        } else if (option.value && option.label) {
            optionElement.value = option.value;
            optionElement.textContent = option.label;
        }
        select.appendChild(optionElement);
    });
    
    // Add custom option for relevant fields
    if (['context', 'action', 'intent'].includes(fieldName)) {
        const customOption = document.createElement('option');
        customOption.value = 'custom';
        customOption.textContent = 'Add New +';
        select.appendChild(customOption);
    }
}

// Input history management
function loadInputHistory() {
    const stored = localStorage.getItem('annotationInputHistory');
    if (stored) {
        inputHistory = JSON.parse(stored);
    }
}

function saveInputHistory() {
    localStorage.setItem('annotationInputHistory', JSON.stringify(inputHistory));
}

function addToHistory(fieldName, value) {
    if (!value || !value.trim()) return;
    
    // Initialize the field array if it doesn't exist
    if (!inputHistory[fieldName]) {
        inputHistory[fieldName] = [];
    }
    
    // Special handling for tags - split by comma and add each tag individually
    if (fieldName === 'tags') {
        const individualTags = value.split(',').map(tag => tag.trim()).filter(tag => tag);
        individualTags.forEach(tag => {
            // Remove if already exists (to move to front)
            const index = inputHistory[fieldName].indexOf(tag);
            if (index > -1) {
                inputHistory[fieldName].splice(index, 1);
            }
            // Add to front
            inputHistory[fieldName].unshift(tag);
            
            // Add to global tags lookup if not present
            if (window.tagsLookup && !window.tagsLookup.has(tag)) {
                if (typeof updateLookup === 'function') {
                    updateLookup(tag);
                } else {
                    window.tagsLookup.add(tag);
                }
            }
        });
    } else {
        // Normal handling for other fields
        // Remove if already exists (to move to front)
        const index = inputHistory[fieldName].indexOf(value);
        if (index > -1) {
            inputHistory[fieldName].splice(index, 1);
        }
        
        // Add to front
        inputHistory[fieldName].unshift(value);
    }
    
    // Keep only last 20 entries
    if (inputHistory[fieldName].length > 20) {
        inputHistory[fieldName] = inputHistory[fieldName].slice(0, 20);
    }
    
    // Save to localStorage
    localStorage.setItem('annotationInputHistory', JSON.stringify(inputHistory));
}

// Recent buttons management
function updateRecentButtons(fieldName) {
    const buttonsContainer = document.getElementById(fieldName + '_recent');
    console.log(`Updating recent buttons for ${fieldName}, container:`, buttonsContainer);
    
    if (!buttonsContainer) {
        console.log(`No container found for ${fieldName}_recent`);
        return;
    }
    
    buttonsContainer.innerHTML = '';
    const recentItems = inputHistory[fieldName] || [];
    console.log(`Recent items for ${fieldName}:`, recentItems);
    
    if (fieldName === 'tags') {
        // For tags, show unique individual tags as recommendations (40 max)
        const uniqueTags = [...new Set(recentItems)];
        uniqueTags.slice(0, 40).forEach(tag => {
            const button = document.createElement('button');
            button.textContent = tag;
            button.className = 'recent-button';
            button.type = 'button';
            button.title = `Add tag: ${tag}`;
            button.onclick = () => {
                const field = document.getElementById(fieldName);
                const currentTags = field.value.split(',').map(t => t.trim()).filter(t => t);
                
                // Only add if tag is not already present
                if (!currentTags.includes(tag)) {
                    if (field.value.trim()) {
                        field.value = field.value.trim() + ', ' + tag;
                    } else {
                        field.value = tag;
                    }
                }
                field.focus();
            };
            buttonsContainer.appendChild(button);
        });
    } else {
        // For other fields, show recent values (10 max for scene)
        const maxItems = fieldName === 'scene' ? 10 : 20;
        recentItems.slice(0, maxItems).forEach(item => {
            const button = document.createElement('button');
            button.textContent = item;
            button.className = 'recent-button';
            button.type = 'button';
            button.title = item; // Full text on hover
            button.onclick = () => {
                const field = document.getElementById(fieldName);
                // For other fields, replace the content
                field.value = item;
                field.focus();
            };
            buttonsContainer.appendChild(button);
        });
    }
    
    console.log(`Added ${buttonsContainer.children.length} buttons for ${fieldName}`);
}

function initializeRecentButtons() {
    // Add some sample data if no history exists
    if (!inputHistory.scene || inputHistory.scene.length === 0) {
        inputHistory.scene = ['battle_intro', 'dialogue_1', 'overworld_town', 'menu_main', 'cutscene_opening'];
    }
    if (!inputHistory.tags || inputHistory.tags.length === 0) {
        inputHistory.tags = ['player_action', 'npc_interaction', 'movement', 'menu_navigation', 'battle', 'dialogue', 'exploration'];
    }
    
    // Context uses dropdown, no recent buttons needed
    updateRecentButtons('scene');
    updateRecentButtons('tags');
}

// Form field navigation
function setupFormFieldNavigation() {
    const fields = ['scene', 'tags', 'description']; // Scene is now a text input again
    
    fields.forEach(fieldName => {
        const field = document.getElementById(fieldName);
        if (!field) return; // Skip if field doesn't exist
        
        // For select fields, we'll handle them differently
        if (field.tagName === 'SELECT') {
            // For dropdowns, we can still use arrow keys but won't interfere with native behavior
            return;
        }
        
        field.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                e.preventDefault();
                
                const history = inputHistory[fieldName];
                if (history.length === 0) return;
                
                if (e.key === 'ArrowUp') {
                    currentHistoryIndex[fieldName] = Math.min(currentHistoryIndex[fieldName] + 1, history.length - 1);
                } else if (e.key === 'ArrowDown') {
                    currentHistoryIndex[fieldName] = Math.max(currentHistoryIndex[fieldName] - 1, -1);
                }
                
                if (currentHistoryIndex[fieldName] >= 0) {
                    field.value = history[currentHistoryIndex[fieldName]];
                } else {
                    field.value = '';
                }
            }
        });
        
        // Reset history index when user starts typing
        field.addEventListener('input', function(e) {
            currentHistoryIndex[fieldName] = -1;
        });
    });
}

// Custom option handling
function handleSelectChange(fieldName) {
    const select = document.getElementById(fieldName);
    const customDiv = document.getElementById(fieldName + '_custom');
    
    if (select.value === 'add_new') {
        customDiv.style.display = 'block';
        document.getElementById(fieldName + '_input').focus();
    } else {
        customDiv.style.display = 'none';
    }
}

function addCustomOption(fieldName) {
    const input = document.getElementById(fieldName + '_input');
    const select = document.getElementById(fieldName);
    const customDiv = document.getElementById(fieldName + '_custom');
    const newValue = input.value.trim();
    
    if (newValue) {
        // Check if option already exists
        const existingOption = Array.from(select.options).find(option => 
            option.value.toLowerCase() === newValue.toLowerCase()
        );
        
        if (!existingOption) {
            // Add new option before "Add New +"
            const newOption = document.createElement('option');
            newOption.value = newValue.toLowerCase().replace(/\s+/g, '_');
            newOption.textContent = newValue;
            
            // Insert before "Add New +" option
            const addNewOption = select.querySelector('option[value="add_new"]');
            select.insertBefore(newOption, addNewOption);
        }
        
        // Select the new/existing option
        const targetValue = existingOption ? existingOption.value : newValue.toLowerCase().replace(/\s+/g, '_');
        select.value = targetValue;
        
        // Hide custom input
        customDiv.style.display = 'none';
        input.value = '';
        
        // Add to input history
        addToHistory(fieldName, newValue);
    }
}

function cancelCustomOption(fieldName) {
    const select = document.getElementById(fieldName);
    const customDiv = document.getElementById(fieldName + '_custom');
    const input = document.getElementById(fieldName + '_input');
    
    select.value = '';
    customDiv.style.display = 'none';
    input.value = '';
}

// Functions referenced in HTML
function handleCustomFieldChange(fieldName) {
    const select = document.getElementById(fieldName);
    const customDiv = document.getElementById(fieldName + '_custom');
    
    if (select.value === 'custom') {
        customDiv.style.display = 'block';
        document.getElementById(fieldName + '_input').focus();
    } else {
        customDiv.style.display = 'none';
    }
}

function addCustomValue(fieldName) {
    const input = document.getElementById(fieldName + '_input');
    const select = document.getElementById(fieldName);
    const customDiv = document.getElementById(fieldName + '_custom');
    const value = input.value.trim();
    
    if (value) {
        // Add new option to select
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value;
        
        // Insert before the "Custom..." option
        const customOption = select.querySelector('option[value="custom"]');
        select.insertBefore(option, customOption);
        
        // Select the new value
        select.value = value;
        
        // Hide custom input and clear it
        customDiv.style.display = 'none';
        input.value = '';
        
        // Add to history
        addToHistory(fieldName, value);
    }
}
