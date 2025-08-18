// --- Tag Input UI Logic ---
let runningTags = [];

function updateTagsListDisplay() {
    const tagsListDiv = document.getElementById('tags-list');
    tagsListDiv.innerHTML = '';
    if (runningTags.length === 0) {
        tagsListDiv.style.display = 'none';
        return;
    }
    tagsListDiv.style.display = 'block';
    runningTags.forEach((tag, idx) => {
        const tagElem = document.createElement('span');
        tagElem.className = 'tag-item';
        tagElem.textContent = tag;
        tagElem.style.marginRight = '6px';
        tagElem.style.background = '#e9ecef';
        tagElem.style.padding = '2px 8px';
        tagElem.style.borderRadius = '12px';
        tagElem.style.display = 'inline-block';
        tagElem.style.fontSize = '13px';
        tagElem.style.cursor = 'pointer';
        tagElem.title = 'Remove tag';
        tagElem.onclick = function() {
            runningTags.splice(idx, 1);
            updateTagsListDisplay();
        };
        tagsListDiv.appendChild(tagElem);
    });
}

function addTagFromInput() {
    const input = document.getElementById('tags');
    let tag = input.value.trim();
    if (!tag) return;
    // Prevent duplicates (case-insensitive)
    if (runningTags.some(t => t.toLowerCase() === tag.toLowerCase())) {
        input.value = '';
        return;
    }
    runningTags.push(tag);
    updateTagsListDisplay();
    input.value = '';
}

document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('tags');
    const addBtn = document.getElementById('add-tag-btn');
    if (input && addBtn) {
        addBtn.addEventListener('click', addTagFromInput);
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addTagFromInput();
            }
        });
        // Listen for autofill selection (datalist)
        input.addEventListener('input', function(e) {
            // If the value matches a datalist option, add it as a tag
            const datalist = document.getElementById('tags-datalist');
            if (datalist) {
                const options = Array.from(datalist.options).map(opt => opt.value.toLowerCase());
                const val = input.value.trim().toLowerCase();
                if (options.includes(val)) {
                    addTagFromInput();
                }
            }
        });
    }
    updateTagsListDisplay();
});

// Utility to get tags for saving annotation
function getCurrentTags() {
    return runningTags.slice();
}
// Frame Grid Annotator - Annotation Management
// Modal handling, annotation copying, and saving

// Copy annotation from a frame
function copyAnnotation(frame) {
    fetch(apiUrl('frame_context', frame))
        .then(res => res.ok ? res.json() : null)
        .then(data => {
            if (data && data.annotations) {
                copiedAnnotation = {
                    context: data.annotations.context || '',
                    scene: data.annotations.scene || '',
                    tags: Array.isArray(data.annotations.tags) ? data.annotations.tags.join(', ') : (data.annotations.tags || ''),
                    action: data.annotations.action || '',
                    intent: data.annotations.intent || '',
                    outcome: data.annotations.outcome || ''
                };
                
                // Visual feedback - flash the frame briefly
                const frameEl = document.getElementById('frame-' + frame);
                if (frameEl) {
                    const original = frameEl.style.background;
                    frameEl.style.background = '#28a745';
                    frameEl.style.color = 'white';
                    setTimeout(() => {
                        frameEl.style.background = original;
                        frameEl.style.color = '';
                    }, 300);
                }
                
                // Update modal title to show copied data is available
                updateModalTitle();
            }
        })
        .catch(err => console.error('Error copying annotation:', err));
}

// Open bulk annotation modal
function openBulkAnnotateModal() {
    if (selectedFramesOrder.length === 0) {
        alert('Please select frames to annotate.');
        return;
    }
    
    isBulkMode = true;
    openModal();
}

// Update modal title to show when copied data is available or bulk mode
function updateModalTitle() {
    const title = document.getElementById('modal-title');
    const bulkNotice = document.getElementById('bulk-mode-notice');
    
    if (isBulkMode) {
        title.textContent = `Bulk Annotate ${selectedFramesOrder.length} Frames`;
        title.style.color = '#fd7e14';
        bulkNotice.style.display = 'block';
    } else if (copiedAnnotation) {
        // Show frame list with copied data indicator
        const frameList = selectedFramesOrder.length > 0 ? `: ${selectedFramesOrder.join(', ')}` : '';
        title.textContent = `Annotate Frames${frameList} (📋 Copied data available)`;
        title.style.color = '#28a745';
        bulkNotice.style.display = 'none';
    } else {
        // Show frame list in normal mode
        const frameList = selectedFramesOrder.length > 0 ? `: ${selectedFramesOrder.join(', ')}` : '';
        title.textContent = `Annotate Frames${frameList}`;
        title.style.color = '';
        bulkNotice.style.display = 'none';
    }
}

// Main modal opening function
function openModal() {
    document.getElementById('annotation-modal').style.display = 'block';
    
    // Get the last selected frame for both snapshot display and annotation logic
    const lastSelectedFrame = selectedFramesOrder.length > 0 ? selectedFramesOrder[selectedFramesOrder.length - 1] : null;
    
    // Update the frame snapshot
    updateModalFrameSnapshot();
    
    // In bulk mode, only populate with defaults, don't load existing annotations
    if (isBulkMode) {
        // Clear all fields first
        document.getElementById('context').value = '';
        document.getElementById('scene').value = '';
        document.getElementById('tags').value = '';
        // document.getElementById('description').value = '';  // Removed description field
        document.getElementById('action').value = '';
        document.getElementById('intent').value = '';
        document.getElementById('outcome').value = '';
        
        // Use recent values as defaults for bulk operations
        const lastContext = inputHistory.context && inputHistory.context.length > 0 ? inputHistory.context[0] : '';
        const lastScene = inputHistory.scene && inputHistory.scene.length > 0 ? inputHistory.scene[0] : '';
        const lastTags = inputHistory.tags && inputHistory.tags.length > 0 ? inputHistory.tags.slice(0, 3).join(', ') : '';
        
        document.getElementById('context').value = lastContext;
        document.getElementById('scene').value = lastScene;
        document.getElementById('tags').value = lastTags;
        
        // Disable action fields in bulk mode
        document.getElementById('action').disabled = true;
        document.getElementById('intent').disabled = true;
        document.getElementById('outcome').disabled = true;
        // document.getElementById('description').disabled = true;  // Removed description field
    } else {
        // Enable all fields in normal mode
        document.getElementById('action').disabled = false;
        document.getElementById('intent').disabled = false;
        document.getElementById('outcome').disabled = false;
        // document.getElementById('description').disabled = false;  // Removed description field
        
        // Normal single/multi-frame annotation logic with priority order:
        // 1. Copied annotation (highest priority)
        // 2. Existing annotations from the selected frame
        // 3. CNN predictions from LAST selected frame (if no copied annotation or existing annotations)
        // 4. Last user annotations (if no copied annotation, existing annotations, and no CNN)
        
        // Priority 1: Check for copied annotation first
        if (copiedAnnotation) {
            document.getElementById('context').value = copiedAnnotation.context;
            document.getElementById('scene').value = copiedAnnotation.scene;
            document.getElementById('tags').value = copiedAnnotation.tags;
            // document.getElementById('description').value = copiedAnnotation.description;  // Removed description field
            document.getElementById('action').value = copiedAnnotation.action;
            document.getElementById('intent').value = copiedAnnotation.intent;
            document.getElementById('outcome').value = copiedAnnotation.outcome;
            // Clear CNN confidence indicators
            document.getElementById('context-confidence').textContent = '';
            document.getElementById('scene-confidence').textContent = '';
        } else if (lastSelectedFrame) {
            // Priority 2, 3 & 4: Fetch LAST selected frame data to check for existing annotations, CNN predictions, or use last annotations
            fetch(apiUrl('frame_context', lastSelectedFrame))
                .then(res => res.ok ? res.json() : null)
                .then(data => {
                    let usedExistingAnnotations = false;
                    let usedCnnPredictions = false;
                    
                    // Clear confidence indicators first
                    document.getElementById('context-confidence').textContent = '';
                    document.getElementById('scene-confidence').textContent = '';
                    
                    // Priority 2: Check for existing annotations first
                    let hasExistingAnnotations = false;
                    if (data && data.annotations) {
                        const existingAnnotations = data.annotations;
                        // Check if we have meaningful existing annotations (not just empty fields)
                        const hasExistingContext = existingAnnotations.context && existingAnnotations.context.trim();
                        const hasExistingScene = existingAnnotations.scene && existingAnnotations.scene.trim();
                        const hasExistingTags = existingAnnotations.tags && existingAnnotations.tags.length > 0;
                        const hasExistingActionType = existingAnnotations.action && existingAnnotations.action.trim();
                        const hasExistingIntent = existingAnnotations.intent && existingAnnotations.intent.trim();
                        const hasExistingOutcome = existingAnnotations.outcome && existingAnnotations.outcome.trim();

                        hasExistingAnnotations = hasExistingContext || hasExistingScene || hasExistingTags || 
                            hasExistingActionType || hasExistingIntent || hasExistingOutcome;
                        if (hasExistingAnnotations) {
                            // Use existing annotations
                            document.getElementById('context').value = existingAnnotations.context || '';
                            document.getElementById('scene').value = existingAnnotations.scene || '';
                            // Handle tags - convert array to comma-delimited string for display
                            const tagsValue = Array.isArray(existingAnnotations.tags) ? 
                                existingAnnotations.tags.join(', ') : (existingAnnotations.tags || '');
                            document.getElementById('tags').value = tagsValue;
                            document.getElementById('action').value = existingAnnotations.action || '';
                            document.getElementById('intent').value = existingAnnotations.intent || '';
                            document.getElementById('outcome').value = existingAnnotations.outcome || '';
                            usedExistingAnnotations = true;
                        }
                    }
                    
                    // Priority 3: Check for CNN predictions if no existing annotations were used
                    if (!hasExistingAnnotations && data && data.cnn_annotations) {
                        const cnnContext = data.cnn_annotations.context;
                        const cnnScene = data.cnn_annotations.scene;

                        // Check if we have high-confidence predictions
                        const hasHighConfidenceContext = cnnContext && cnnContext.confidence > 0.5;
                        const hasHighConfidenceScene = cnnScene && cnnScene.confidence > 0.5;

                        // Use CNN predictions when available with high confidence
                        if (hasHighConfidenceContext || hasHighConfidenceScene) {
                            if (hasHighConfidenceContext) {
                                document.getElementById('context').value = cnnContext.prediction;
                                document.getElementById('context-confidence').textContent = `(CNN: ${(cnnContext.confidence * 100).toFixed(1)}%)`;
                            } else {
                                document.getElementById('context').value = '';
                                document.getElementById('context-confidence').textContent = '';
                            }
                            if (hasHighConfidenceScene) {
                                document.getElementById('scene').value = cnnScene.prediction;
                                document.getElementById('scene-confidence').textContent = `(CNN: ${(cnnScene.confidence * 100).toFixed(1)}%)`;
                            } else {
                                document.getElementById('scene').value = '';
                                document.getElementById('scene-confidence').textContent = '';
                            }
                            // Clear tags and action fields when using CNN predictions
                            document.getElementById('tags').value = '';
                            document.getElementById('action').value = '';
                            document.getElementById('intent').value = '';
                            document.getElementById('outcome').value = '';
                            usedCnnPredictions = true;
                        }
                    }
                    
                    // Priority 4: Use last user annotations if no existing annotations or CNN predictions were used
                    if (!usedExistingAnnotations && !usedCnnPredictions) {
                        const lastContext = inputHistory.context && inputHistory.context.length > 0 ? inputHistory.context[0] : '';
                        const lastScene = inputHistory.scene && inputHistory.scene.length > 0 ? inputHistory.scene[0] : '';
                        const lastTags = inputHistory.tags && inputHistory.tags.length > 0 ? inputHistory.tags.slice(0, 3).join(', ') : '';
                        
                        document.getElementById('context').value = lastContext;
                        document.getElementById('scene').value = lastScene;
                        document.getElementById('tags').value = lastTags;
                        // document.getElementById('description').value = lastDescription;  // Removed description field
                    }
                    
                    // Leave action fields empty unless populated by copied annotation or existing annotations
                    if (!copiedAnnotation && !usedExistingAnnotations) {
                        document.getElementById('action').value = '';
                        document.getElementById('intent').value = '';
                        document.getElementById('outcome').value = '';
                    }
                })
                .catch(err => {
                    console.error('Error checking frame annotations:', err);
                    // Fallback: use last annotations
                    const lastContext = inputHistory.context && inputHistory.context.length > 0 ? inputHistory.context[0] : '';
                    const lastScene = inputHistory.scene && inputHistory.scene.length > 0 ? inputHistory.scene[0] : '';
                    const lastTags = inputHistory.tags && inputHistory.tags.length > 0 ? inputHistory.tags.slice(0, 3).join(', ') : '';
                    
                    document.getElementById('context').value = lastContext;
                    document.getElementById('scene').value = lastScene;
                    document.getElementById('tags').value = lastTags;
                    // document.getElementById('description').value = lastDescription;  // Removed description field
                    // Leave action fields empty
                    document.getElementById('action').value = '';
                    document.getElementById('intent').value = '';
                    document.getElementById('outcome').value = '';
                });
        } else {
            // No frames selected - use priority order: copied annotation first, then last annotations
            if (copiedAnnotation) {
                document.getElementById('context').value = copiedAnnotation.context;
                document.getElementById('scene').value = copiedAnnotation.scene;
                document.getElementById('tags').value = copiedAnnotation.tags;
                // document.getElementById('description').value = copiedAnnotation.description;  // Removed description field
                document.getElementById('action').value = copiedAnnotation.action;
                document.getElementById('intent').value = copiedAnnotation.intent;
                document.getElementById('outcome').value = copiedAnnotation.outcome;
            } else {
                // Use last annotations as fallback
                const lastContext = inputHistory.context && inputHistory.context.length > 0 ? inputHistory.context[0] : '';
                const lastScene = inputHistory.scene && inputHistory.scene.length > 0 ? inputHistory.scene[0] : '';
                const lastTags = inputHistory.tags && inputHistory.tags.length > 0 ? inputHistory.tags.slice(0, 3).join(', ') : '';
                const lastDescription = inputHistory.description && inputHistory.description.length > 0 ? inputHistory.description[0] : '';
                
                document.getElementById('context').value = lastContext;
                document.getElementById('scene').value = lastScene;
                document.getElementById('tags').value = lastTags;
                document.getElementById('description').value = lastDescription;
                // Leave action fields empty
                document.getElementById('action').value = '';
                document.getElementById('intent').value = '';
                document.getElementById('outcome').value = '';
            }
        }
    }
    
    // Populate recent buttons - context uses dropdown, scene and tags use recent buttons
    updateRecentButtons('scene');
    updateRecentButtons('tags');
    
    document.getElementById('scene').focus();
    
    // Reset history indices
    Object.keys(currentHistoryIndex).forEach(key => {
        currentHistoryIndex[key] = -1;
    });
    
    // Set up form field navigation if not already done
    setupFormFieldNavigation();
    
    // Update modal title
    updateModalTitle();
}

// Function to update the frame snapshot in the modal
function updateModalFrameSnapshot() {
    const modalTitle = document.getElementById('modal-title');
    const buttonSequence = document.getElementById('frame-buttons-display');
    
    if (selectedFramesOrder.length === 0) {
        // Reset displays if no frames selected
        document.getElementById('snapshot-image').src = '';
        modalTitle.textContent = 'Annotate Frames';
        buttonSequence.textContent = 'No buttons';
        return;
    }
    
    // Update the title with selected frames list
    modalTitle.textContent = `Annotate Frames: ${selectedFramesOrder.join(', ')}`;
    
    // Show the last selected frame (most recently selected)
    const lastSelectedFrame = selectedFramesOrder[selectedFramesOrder.length - 1];
    const snapshotImage = document.getElementById('snapshot-image');
    
    // Update the image source
    snapshotImage.src = apiUrl('frame_image', lastSelectedFrame);
    
    // Load and display button events for the specific frame
    buttonSequence.textContent = 'Loading button events...';
    fetch(apiUrl('frame_context', lastSelectedFrame))
        .then(res => res.ok ? res.json() : null)
        .then(data => {
            if (data && data.buttons && Array.isArray(data.buttons)) {
                // Filter out 'None' values and collect actual button presses
                const actualButtons = data.buttons.filter(button => button !== 'None');
                
                if (actualButtons.length === 0) {
                    buttonSequence.textContent = 'No buttons';
                } else {
                    buttonSequence.textContent = actualButtons.join(', ');
                }
            } else {
                buttonSequence.textContent = 'No button data available';
            }
        })
        .catch(err => {
            console.error('Error loading button events:', err);
            buttonSequence.textContent = 'Error loading button events';
        });
}

// Close modal function
function closeModal() {
    document.getElementById('annotation-modal').style.display = 'none';
    document.getElementById('annotation-form').reset();
    
    // Reset bulk mode
    isBulkMode = false;
    
    // Re-enable all fields
    document.getElementById('action').disabled = false;
    document.getElementById('intent').disabled = false;
    document.getElementById('outcome').disabled = false;
    // document.getElementById('description').disabled = false;  // Removed description field
    
    // Hide any custom input areas
    document.getElementById('context_custom').style.display = 'none';
    document.getElementById('action_custom').style.display = 'none';
    document.getElementById('intent_custom').style.display = 'none';
    
    // Clear custom input fields
    document.getElementById('context_input').value = '';
    document.getElementById('action_input').value = '';
    document.getElementById('intent_input').value = '';
}

// Clear copied annotation data
function clearCopiedAnnotation() {
    copiedAnnotation = null;
    updateModalTitle();
    // Clear the form fields
    document.getElementById('context').value = '';
    document.getElementById('scene').value = '';
    document.getElementById('tags').value = '';
    // document.getElementById('description').value = '';  // Removed description field
    document.getElementById('action').value = '';
    document.getElementById('intent').value = '';
    document.getElementById('outcome').value = '';
}

// Mark selected frames as complete (bulk action)
function markSelectedComplete() {
    if (selectedFramesOrder.length === 0) {
        alert('Please select frames to mark as complete.');
        return;
    }
    
    const framesList = selectedFramesOrder.slice();
    const annotation = { complete: true };
    
    fetch(apiUrl('annotate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            frames: framesList,
            annotation: annotation
        })
    })
    .then(res => {
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        console.log('Frames marked as complete:', data);
        
        // Update UI to show frames as completed
        framesList.forEach(frame => {
            markFrameAsAnnotated(frame);
        });
        
        // Store the last annotated frame for position tracking
        localStorage.setItem('lastAnnotatedFrame', Math.max(...framesList));
        
        // Clear selection
        selectedFrames.clear();
        selectedFramesOrder = [];
        framesList.forEach(frame => {
            const el = document.getElementById('frame-' + frame);
            if (el) el.classList.remove('selected');
        });
        lastSelectedFrame = null;
        updateBulkAnnotateButton();
        
        // Silent success - no alert message needed
    })
    .catch(err => {
        console.error('Error marking frames as complete:', err);
        alert('Error marking frames as complete. Please try again.');
    });
}

// Mark complete and save annotation (from modal)
function markCompleteAndSave() {
    const context = document.getElementById('context').value;
    const scene = document.getElementById('scene').value;
    const tagsInput = document.getElementById('tags').value;
    const action = document.getElementById('action').value;
    const intent = document.getElementById('intent').value;
    const outcome = document.getElementById('outcome').value;
    
    // Convert comma-delimited tags to array
    const tags = getCurrentTags();

    const annotation = {
        context: context || '',
        scene: scene || '',
        tags: tags,
        description: '',  // Keep for backend compatibility
        action: action || '',
        intent: intent || '',
        outcome: outcome || '',
        complete: true  // Mark as complete
    };
    
    saveAnnotationWithComplete(annotation);
}

// Save annotation with completion status
function saveAnnotationWithComplete(annotation) {
    const framesList = selectedFramesOrder.slice();
    
    if (framesList.length === 0) {
        alert('No frames selected for annotation.');
        return;
    }
    
    fetch(apiUrl('annotate', ), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            frames: framesList,
            annotation: annotation
        })
    })
    .then(res => {
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        console.log('Annotation saved:', data);
        
        // Add to input history (excluding complete flag)
        Object.keys(annotation).forEach(key => {
            if (key !== 'complete' && annotation[key]) {
                // Handle tags array specially - convert to string for history
                if (key === 'tags' && Array.isArray(annotation[key])) {
                    const tagsString = annotation[key].join(', ');
                    if (tagsString.trim()) {
                        addToHistory(key, tagsString);
                    }
                } else if (typeof annotation[key] === 'string') {
                    addToHistory(key, annotation[key]);
                }
            }
        });
        
        // Update UI based on completion status
        if (annotation.complete) {
            framesList.forEach(frame => {
                markFrameAsAnnotated(frame);
                // Store the last annotated frame for position tracking
                localStorage.setItem('lastAnnotatedFrame', Math.max(...framesList));
            });
        } else {
            // Check if annotation has meaningful data to mark as partial
            const hasData = annotation.context || annotation.scene || 
                          (annotation.tags && annotation.tags.length > 0) ||
                          annotation.action || annotation.intent || annotation.outcome;
            
            if (hasData) {
                framesList.forEach(frame => {
                    markFrameAsPartial(frame);
                });
            }
        }
        
        // Clear selection and close modal
        selectedFrames.clear();
        selectedFramesOrder = [];
        framesList.forEach(frame => {
            const el = document.getElementById('frame-' + frame);
            if (el) el.classList.remove('selected');
        });
        lastSelectedFrame = null;
        closeModal();
        updateBulkAnnotateButton();
        updateCompletionStats();
        
        // Silent success - no alert message needed
    })
    .catch(err => {
        console.error('Error saving annotation:', err);
        alert('Error saving annotation. Please try again.');
    });
}

// Reset annotations for selected frames
function resetAnnotations() {
    const framesToReset = selectedFramesOrder.slice();
    if (framesToReset.length === 0) {
        alert('Please select at least one frame to reset annotations for.');
        return;
    }
    
    const confirmReset = confirm(`Are you sure you want to reset annotations for ${framesToReset.length} frame(s)? This will clear all annotation data for the selected frames.`);
    if (!confirmReset) {
        return;
    }
    
    // Create empty annotation object
    const emptyAnnotation = {
        context: '',
        scene: '',
        tags: [],
        description: '',
        action: '',
        intent: '',
        outcome: '',
        complete: false
    };
    
    console.log('Resetting annotations for frames:', framesToReset);
    
    fetch(apiUrl('annotate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frames: framesToReset, annotation: emptyAnnotation })
    }).then(res => {
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    }).then(data => {
        console.log('Annotations reset:', data);
        
        // Update UI to remove annotation indicators
        framesToReset.forEach(frame => {
            const frameDiv = document.getElementById('frame-' + frame);
            if (frameDiv) {
                frameDiv.classList.remove('annotated');
            }
        });
        
        // Clear selection
        selectedFrames.clear();
        selectedFramesOrder = [];
        framesToReset.forEach(frame => {
            const el = document.getElementById('frame-' + frame);
            if (el) el.classList.remove('selected');
        });
        lastSelectedFrame = null;
        updateBulkAnnotateButton();
        updateCompletionStats();
        
        alert(`Annotations reset for ${framesToReset.length} frame(s).`);
    }).catch(err => {
        console.error('Error resetting annotations:', err);
        alert('Error resetting annotations: ' + err.message);
    });
}

// Form submission setup
function setupFormSubmission() {
    document.getElementById('annotation-form').onsubmit = function(e) {
        e.preventDefault();
        
        // Check if frames are selected
        const framesToUpdate = selectedFramesOrder.slice();
        if (framesToUpdate.length === 0) {
            alert('Please select at least one frame to annotate.');
            return;
        }
        
        let context = document.getElementById('context').value;
        let scene = document.getElementById('scene').value;
        let action = document.getElementById('action').value;
        let intent = document.getElementById('intent').value;
        let outcome = document.getElementById('outcome').value;

        // Normalize values: replace spaces with underscores and lowercase if capitals or spaces present
        [context, scene, action, intent, outcome] = [context, scene, action, intent, outcome].map(val => {
            return (/[A-Z ]/.test(val)) ? val.toLowerCase().replace(/\s+/g, '_') : val;
        });
        
        // Convert comma-delimited tags to array
        const tags = getCurrentTags();
        
        // Build annotation object (without complete flag - regular save)
        let annotation;
        if (isBulkMode) {
            // In bulk mode, only include context, scene, and tags
            annotation = { 
                context, 
                scene, 
                tags,
                description: '',  // Keep for backend compatibility
                action: '', // Clear action fields in bulk mode
                intent: '',
                outcome: '',
                complete: false // Regular save, not complete
            };
        } else {
            // Normal mode - include all fields
            annotation = { 
                context, 
                scene, 
                tags, 
                description: '',  // Keep for backend compatibility
                action: action || '',
                intent: intent || '',
                outcome: outcome || '',
                complete: false // Regular save, not complete
            };
        }
        
        // Use the new save function
        saveAnnotationWithComplete(annotation);
    };
}

// Inject to Database function (placeholder)
function injectToDatabase() {
    alert('Inject to Database functionality not implemented yet.');
}

// Toggle visibility of annotated frames
function toggleAnnotatedFrames() {
    const button = event.target;
    const annotatedFrames = document.querySelectorAll('.frame.annotated');
    
    if (!annotatedFramesHidden) {
        // Hide annotated frames
        annotatedFrames.forEach(frame => {
            frame.style.display = 'none';
        });
        button.textContent = '👁️ Show Annotated Frames';
        button.title = 'Show annotated frames';
        annotatedFramesHidden = true;
    } else {
        // Show annotated frames
        annotatedFrames.forEach(frame => {
            frame.style.display = 'block';
        });
        button.textContent = '👁️ Hide Annotated Frames';
        button.title = 'Hide annotated frames';
        annotatedFramesHidden = false;
    }
}
