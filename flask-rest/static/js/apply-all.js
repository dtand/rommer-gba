// Store field configurations
let applyFieldCounter = 0;

function openApplyAllModal() {
    console.log('Modal opening');
    
    // Check if frames are selected
    if (typeof selectedFramesOrder === 'undefined' || selectedFramesOrder.length === 0) {
        alert('Please select frames to apply field values to.');
        return;
    }
    
    // Update frame count display
    document.getElementById('apply-all-frame-count').textContent = selectedFramesOrder.length;
    
    // Reset form
    const container = document.getElementById('apply-fields-container');
    container.innerHTML = '';
    applyFieldCounter = 0;
    
    // Add first field
    addApplyField();
    
    // Show modal
    document.getElementById('apply-all-modal').style.display = 'block';
}

function closeApplyAllModal() {
    console.log('Modal closing');
    document.getElementById('apply-all-modal').style.display = 'none';
    const container = document.getElementById('apply-fields-container');
    container.innerHTML = '';
    applyFieldCounter = 0;
}

// Add a new field to apply
function addApplyField() {
    const container = document.getElementById('apply-fields-container');
    const fieldId = ++applyFieldCounter;
    
    const fieldDiv = document.createElement('div');
    fieldDiv.className = 'apply-field-row';
    fieldDiv.id = 'apply-field-row-' + fieldId;
    fieldDiv.style.cssText = 'border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin: 10px 0; background: #f8f9fa;';
    
    const headerHtml = '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">' +
        '<h4 style="margin: 0; color: #495057;">Field ' + fieldId + '</h4>' +
        (fieldId > 1 ? '<button type="button" onclick="removeApplyField(' + fieldId + ')" style="background: #dc3545; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 12px;">Remove</button>' : '') +
        '</div>';
    
    const selectHtml = '<div class="form-row" style="margin-bottom: 10px;">' +
        '<label for="apply-field-' + fieldId + '">Field to Apply:</label>' +
        '<select id="apply-field-' + fieldId + '" onchange="updateApplyFieldInput(' + fieldId + ')" style="width: 100%; padding: 8px; margin: 5px 0;" required>' +
        '<option value="">Select field...</option>' +
        '<option value="context">Context</option>' +
        '<option value="scene">Scene</option>' +
        '<option value="tags">Tags</option>' +
        '</select>' +
        '</div>';
    
    const valueHtml = '<div class="form-row" id="apply-value-row-' + fieldId + '" style="display: none;">' +
        '<label for="apply-value-' + fieldId + '" id="apply-value-label-' + fieldId + '">Value:</label>' +
        '<div id="apply-value-container-' + fieldId + '"></div>' +
        '</div>';
    
    fieldDiv.innerHTML = headerHtml + selectHtml + valueHtml;
    container.appendChild(fieldDiv);
    
    // Disable "Add Another Field" button if we have 3 fields for now
    const addButton = document.getElementById('add-field-btn');
    if (addButton && container.children.length >= 3) {
        addButton.style.display = 'none';
    }
}

// Remove a field
function removeApplyField(fieldId) {
    const fieldRow = document.getElementById('apply-field-row-' + fieldId);
    if (fieldRow) {
        fieldRow.remove();
        
        // Re-enable "Add Another Field" button
        const container = document.getElementById('apply-fields-container');
        const addButton = document.getElementById('add-field-btn');
        if (addButton && container.children.length < 3) {
            addButton.style.display = 'inline-block';
        }
    }
}

// Update the value input based on selected field
function updateApplyFieldInput(fieldId) {
    const field = document.getElementById('apply-field-' + fieldId).value;
    const valueRow = document.getElementById('apply-value-row-' + fieldId);
    const valueContainer = document.getElementById('apply-value-container-' + fieldId);
    
    if (!field) {
        valueRow.style.display = 'none';
        return;
    }
    
    valueRow.style.display = 'block';
    
    let inputHtml = '';
    switch (field) {
        case 'context':
            inputHtml = generateContextInput(fieldId);
            break;
        case 'scene':
            inputHtml = generateSceneInput(fieldId);
            break;
        case 'tags':
            inputHtml = generateTagsInput(fieldId);
            break;
        case 'action_type':
            inputHtml = generateActionTypeInput(fieldId);
            break;
        case 'intent':
            inputHtml = generateIntentInput(fieldId);
            break;
        case 'outcome':
            inputHtml = generateOutcomeInput(fieldId);
            break;
        default:
            inputHtml = generateDefaultInput(fieldId);
    }
    
    valueContainer.innerHTML = inputHtml;
    
    // Add quick-select buttons for scene and tags fields
    if (field === 'scene') {
        updateApplyRecentButtons('scene', fieldId);
    } else if (field === 'tags') {
        updateApplyRecentButtons('tags', fieldId);
    }
}

// Generate context dropdown input
function generateContextInput(fieldId) {
    let inputHtml = '<select id="apply-value-' + fieldId + '" style="width: 100%; padding: 8px;" required>' +
        '<option value="">Select context...</option>';
    
    // Use global annotation config for context options
    if (window.annotationConfig && window.annotationConfig.context_options) {
        window.annotationConfig.context_options.forEach(option => {
            inputHtml += '<option value="' + option.value + '">' + option.label + '</option>';
        });
    } else {
        // Fallback options if config not loaded
        const fallbackOptions = [
            { value: 'battle', label: 'Battle' },
            { value: 'main_menu', label: 'Main Menu' },
            { value: 'overworld', label: 'Overworld' },
            { value: 'dialogue', label: 'Dialogue' }
        ];
        fallbackOptions.forEach(option => {
            inputHtml += '<option value="' + option.value + '">' + option.label + '</option>';
        });
    }
    
    inputHtml += '</select>';
    return inputHtml;
}

// Generate action type dropdown input
function generateActionTypeInput(fieldId) {
    let inputHtml = '<select id="apply-value-' + fieldId + '" style="width: 100%; padding: 8px;" required>' +
        '<option value="">Select action type...</option>';
    
    // Use global annotation config for action_type options
    if (window.annotationConfig && window.annotationConfig.action_type_options) {
        window.annotationConfig.action_type_options.forEach(option => {
            inputHtml += '<option value="' + option.value + '">' + option.label + '</option>';
        });
    } else {
        // Fallback options if config not loaded
        const fallbackOptions = [
            { value: 'menu_navigation', label: 'Menu Navigation' },
            { value: 'combat', label: 'Combat' },
            { value: 'dialogue_choice', label: 'Dialogue Choice' },
            { value: 'exploration', label: 'Exploration' }
        ];
        fallbackOptions.forEach(option => {
            inputHtml += '<option value="' + option.value + '">' + option.label + '</option>';
        });
    }
    
    inputHtml += '</select>';
    return inputHtml;
}

// Generate intent dropdown input
function generateIntentInput(fieldId) {
    let inputHtml = '<select id="apply-value-' + fieldId + '" style="width: 100%; padding: 8px;" required>' +
        '<option value="">Select intent...</option>';
    
    // Use global annotation config for intent options
    if (window.annotationConfig && window.annotationConfig.intent_options) {
        window.annotationConfig.intent_options.forEach(option => {
            inputHtml += '<option value="' + option.value + '">' + option.label + '</option>';
        });
    } else {
        // Fallback options if config not loaded
        const fallbackOptions = [
            { value: 'progress', label: 'Progress' },
            { value: 'explore_area', label: 'Explore Area' },
            { value: 'access_menu', label: 'Access Menu' },
            { value: 'select_option', label: 'Select Option' }
        ];
        fallbackOptions.forEach(option => {
            inputHtml += '<option value="' + option.value + '">' + option.label + '</option>';
        });
    }
    
    inputHtml += '</select>';
    return inputHtml;
}

// Generate outcome dropdown input
function generateOutcomeInput(fieldId) {
    let inputHtml = '<select id="apply-value-' + fieldId + '" style="width: 100%; padding: 8px;" required>' +
        '<option value="">Select outcome...</option>';
    
    // Use global annotation config for outcome options
    if (window.annotationConfig && window.annotationConfig.outcome_options) {
        window.annotationConfig.outcome_options.forEach(option => {
            inputHtml += '<option value="' + option.value + '">' + option.label + '</option>';
        });
    } else {
        // Fallback options if config not loaded
        const fallbackOptions = [
            { value: 'success', label: 'Success' },
            { value: 'failure', label: 'Failure' },
            { value: 'partial_success', label: 'Partial Success' },
            { value: 'ongoing', label: 'Ongoing' }
        ];
        fallbackOptions.forEach(option => {
            inputHtml += '<option value="' + option.value + '">' + option.label + '</option>';
        });
    }
    
    inputHtml += '</select>';
    return inputHtml;
}

// Generate scene text input
function generateSceneInput(fieldId) {
    return '<input type="text" id="apply-value-' + fieldId + '" placeholder="Enter scene value" style="width: 100%; padding: 8px;" required>' +
           '<div id="apply-value-' + fieldId + '-recent" class="recent-buttons-container" style="margin-top: 5px;"></div>';
}

// Generate tags text input with comma separation hint
function generateTagsInput(fieldId) {
    return '<input type="text" id="apply-value-' + fieldId + '" placeholder="Enter tags separated by commas" style="width: 100%; padding: 8px;" required>' +
           '<div id="apply-value-' + fieldId + '-recent" class="recent-buttons-container" style="margin-top: 5px;"></div>';
}

// Generate default text input for unknown field types
function generateDefaultInput(fieldId) {
    return '<input type="text" id="apply-value-' + fieldId + '" placeholder="Enter value" style="width: 100%; padding: 8px;" required>';
}

// Helper function to get dropdown options from config or fallback
function getDropdownOptions(configKey, fallbackOptions) {
    if (window.annotationConfig && window.annotationConfig[configKey]) {
        return window.annotationConfig[configKey];
    }
    return fallbackOptions;
}

// Helper function to generate dropdown HTML from options array
function generateDropdownFromOptions(fieldId, placeholder, options) {
    let inputHtml = '<select id="apply-value-' + fieldId + '" style="width: 100%; padding: 8px;" required>' +
        '<option value="">' + placeholder + '</option>';
    
    options.forEach(option => {
        // Handle both object format {value, label} and string format
        if (typeof option === 'object' && option.value && option.label) {
            inputHtml += '<option value="' + option.value + '">' + option.label + '</option>';
        } else if (typeof option === 'string') {
            inputHtml += '<option value="' + option + '">' + option + '</option>';
        }
    });
    
    inputHtml += '</select>';
    return inputHtml;
}

// Update recent buttons for Apply All modal fields
function updateApplyRecentButtons(fieldName, fieldId) {
    const buttonsContainer = document.getElementById('apply-value-' + fieldId + '-recent');
    
    if (!buttonsContainer) {
        console.log(`No container found for apply-value-${fieldId}-recent`);
        return;
    }
    
    // Load input history from localStorage
    const stored = localStorage.getItem('annotationInputHistory');
    const inputHistory = stored ? JSON.parse(stored) : {};
    
    buttonsContainer.innerHTML = '';
    const recentItems = inputHistory[fieldName] || [];
    
    if (fieldName === 'tags') {
        // For tags, show unique individual tags as recommendations
        const uniqueTags = [...new Set(recentItems)];
        uniqueTags.slice(0, 20).forEach(tag => {
            const button = document.createElement('button');
            button.textContent = tag;
            button.className = 'recent-button';
            button.type = 'button';
            button.title = `Add tag: ${tag}`;
            button.style.cssText = 'margin: 2px; padding: 4px 8px; background: #e9ecef; border: 1px solid #ced4da; border-radius: 3px; cursor: pointer; font-size: 12px;';
            button.onclick = () => {
                const field = document.getElementById('apply-value-' + fieldId);
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
    } else if (fieldName === 'scene') {
        // For scene, show recent values
        recentItems.slice(0, 10).forEach(item => {
            const button = document.createElement('button');
            button.textContent = item;
            button.className = 'recent-button';
            button.type = 'button';
            button.title = item;
            button.style.cssText = 'margin: 2px; padding: 4px 8px; background: #e9ecef; border: 1px solid #ced4da; border-radius: 3px; cursor: pointer; font-size: 12px;';
            button.onclick = () => {
                const field = document.getElementById('apply-value-' + fieldId);
                field.value = item;
                field.focus();
            };
            buttonsContainer.appendChild(button);
        });
    }
    
    console.log(`Added ${buttonsContainer.children.length} buttons for ${fieldName} field ${fieldId}`);
}

// Apply all fields
function applyAllFields() {
    const container = document.getElementById('apply-fields-container');
    const fieldRows = container.children;
    
    if (fieldRows.length === 0) {
        alert('Please add at least one field to apply.');
        return;
    }
    
    if (typeof selectedFramesOrder === 'undefined' || selectedFramesOrder.length === 0) {
        alert('No frames selected.');
        return;
    }
    
    // Collect all field-value pairs
    const fieldsToApply = {};
    
    for (let i = 0; i < fieldRows.length; i++) {
        const fieldRow = fieldRows[i];
        const fieldId = fieldRow.id.split('-').pop();
        
        const fieldSelect = document.getElementById('apply-field-' + fieldId);
        const valueInput = document.getElementById('apply-value-' + fieldId);
        
        const field = fieldSelect ? fieldSelect.value : '';
        const value = valueInput ? valueInput.value : '';
        
        if (!field || !value) {
            alert('Please select a field and enter a value for Field ' + fieldId + '.');
            return;
        }
        
        // Check for duplicates
        if (fieldsToApply[field]) {
            alert('Duplicate field "' + field + '" detected. Please remove duplicates.');
            return;
        }
        
        fieldsToApply[field] = value;
    }
    
    // Apply the fields to all selected frames
    applyMultipleFieldsToFrames(fieldsToApply, selectedFramesOrder.slice());
}

// Apply multiple fields to selected frames
function applyMultipleFieldsToFrames(fields, frames) {
    fetch(apiUrl('apply_multiple_fields'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            frames: frames,
            fields: fields
        })
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('HTTP error! status: ' + res.status);
        }
        return res.json();
    })
    .then(data => {
        console.log('Fields applied:', data);
        
        // Mark frames as partial
        frames.forEach(frameId => {
            if (typeof markFrameAsPartial === 'function') {
                markFrameAsPartial(frameId);
            }
        });
        
        // Update completion stats
        if (typeof updateCompletionStats === 'function') {
            updateCompletionStats();
        }
        
        // Close modal
        closeApplyAllModal();
        
        // Clear selection
        if (typeof selectedFrames !== 'undefined') {
            selectedFrames.clear();
            selectedFramesOrder = [];
            frames.forEach(frame => {
                const el = document.getElementById('frame-' + frame);
                if (el) el.classList.remove('selected');
            });
        }
        
        if (typeof lastSelectedFrame !== 'undefined') {
            lastSelectedFrame = null;
        }
        
        if (typeof updateBulkAnnotateButton === 'function') {
            updateBulkAnnotateButton();
        }
        
        // Show success message
        alert('Applied ' + Object.keys(fields).join(', ') + ' to ' + frames.length + ' frame(s)');
    })
    .catch(err => {
        console.error('Error applying fields:', err);
        alert('Error applying fields. Please try again.');
    });
}

// Expose globally
window.openApplyAllModal = openApplyAllModal;
window.closeApplyAllModal = closeApplyAllModal;
window.addApplyField = addApplyField;
window.removeApplyField = removeApplyField;
window.updateApplyFieldInput = updateApplyFieldInput;
window.applyAllFields = applyAllFields;

console.log('Functions exposed:', typeof window.openApplyAllModal);
