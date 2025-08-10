// Frame Grid Annotator - Sidebar Management
// Sidebar display, updates, and scrolling behavior

let scrollTimeout;

// Update sidebar with frame information
function updateSidebar(frameId, isSelected = false, isLastAnnotated = false) {
    const previewImage = document.getElementById('preview-image');
    const previewPlaceholder = document.getElementById('preview-placeholder');
    const previewLabel = document.getElementById('preview-frame-label');
    const infoContent = document.getElementById('info-content');
    
    if (!frameId) {
        // Clear sidebar - show last annotated frame if available and no selections/hover
        if (lastAnnotatedFrame && !currentHoveredFrame && selectedFramesOrder.length === 0) {
            updateSidebar(lastAnnotatedFrame, false, true);
            return;
        }
        
        previewImage.style.display = 'none';
        previewPlaceholder.style.display = 'flex';
        previewLabel.textContent = 'Select or hover a frame';
        infoContent.innerHTML = '<div style="color: #6c757d;">Hover over or select a frame to see details</div>';
        return;
    }
    
    // Update image
    previewImage.src = apiUrl('frame_image', frameId);
    previewImage.style.display = 'block';
    previewPlaceholder.style.display = 'none';
    
    // Update label
    if (isSelected) {
        previewLabel.textContent = `Frame ${frameId} (Selected)`;
        previewLabel.style.color = '#007bff';
    } else if (isLastAnnotated) {
        previewLabel.textContent = `Frame ${frameId} (Last Annotated)`;
        previewLabel.style.color = '#28a745';
    } else {
        previewLabel.textContent = `Frame ${frameId} (Hovered)`;
        previewLabel.style.color = '#495057';
    }
    
    // Load and display frame information - single API call only
    infoContent.innerHTML = '<div style="color: #6c757d;">Loading frame information...</div>';
    
    fetch(apiUrl('frame_context', frameId))
        .then(res => res.ok ? res.json() : null)
        .then(data => {
            if (!data) {
                infoContent.innerHTML = '<div style="color: #dc3545;">No data available for this frame</div>';
                return;
            }
            
            let html = `<div style="margin-bottom: 15px;"><strong>Frame ${frameId} Data</strong></div>`;
            
            // Display Frames in Set
            if (data.frames_in_set) {
                html += `<div style="margin-bottom: 10px;">
                    <strong>Frames in Set:</strong><br>
                    <span style="font-family: monospace; color: #495057;">${data.frames_in_set.join(', ')}</span>
                </div>`;
            }
            
            // Display Buttons
            html += `<div style="margin-bottom: 15px;">
                <strong>Button Events:</strong><br>`;
            
            if (data.buttons && data.buttons.length > 0) {
                data.buttons.forEach((button, index) => {
                    const buttonText = Array.isArray(button) ? button.join('+') : (button === 'None' ? 'None' : button);
                    html += `<div style="font-family: monospace; color: #495057; margin: 2px 0;">[${index}]: ${buttonText}</div>`;
                });
            } else {
                html += '<div style="color: #6c757d; font-style: italic;">No button events recorded</div>';
            }
            html += '</div>';
            
            // Display Annotation Information if present
            if (data.annotations && (data.annotations.context || data.annotations.scene || data.annotations.tags || data.annotations.description)) {
                html += `<div style="margin-bottom: 15px; padding: 10px; background: #e7f3ff; border-radius: 4px; border-left: 4px solid #007bff;">
                    <strong>Annotations:</strong><br>`;
                
                if (data.annotations.context) {
                    html += `<div style="margin: 3px 0;"><strong>Context:</strong> ${data.annotations.context}</div>`;
                }
                if (data.annotations.scene) {
                    html += `<div style="margin: 3px 0;"><strong>Scene:</strong> ${data.annotations.scene}</div>`;
                }
                if (data.annotations.tags) {
                    const tagsDisplay = Array.isArray(data.annotations.tags) ? data.annotations.tags.join(', ') : data.annotations.tags;
                    html += `<div style="margin: 3px 0;"><strong>Tags:</strong> ${tagsDisplay}</div>`;
                }
                if (data.annotations.description) {
                    html += `<div style="margin: 3px 0;"><strong>Description:</strong> ${data.annotations.description}</div>`;
                }
                
                // Show action data if present
                if (data.annotations.action_type || data.annotations.intent || data.annotations.outcome) {
                    html += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #b3d7ff;">
                        <strong>Action:</strong><br>`;
                    if (data.annotations.action_type) html += `<div style="margin: 2px 0;"><strong>Type:</strong> ${data.annotations.action_type}</div>`;
                    if (data.annotations.intent) html += `<div style="margin: 2px 0;"><strong>Intent:</strong> ${data.annotations.intent}</div>`;
                    if (data.annotations.outcome) html += `<div style="margin: 2px 0;"><strong>Outcome:</strong> ${data.annotations.outcome}</div>`;
                    html += '</div>';
                }
                
                html += `<div style="margin-top: 8px; font-size: 11px; color: #6c757d;">
                    <em>Ctrl+Click to copy annotation</em>
                </div></div>`;
            }
            
            // Display CNN Predictions if available and no annotations
            if (data.cnn_annotations && (!data.annotations || Object.keys(data.annotations).length === 0)) {
                html += `<div style="margin-bottom: 15px; padding: 10px; background: #fff3cd; border-radius: 4px; border-left: 4px solid #ffc107;">
                    <strong>CNN Predictions:</strong><br>`;
                
                if (data.cnn_annotations.context) {
                    html += `<div style="margin: 3px 0;"><strong>Context:</strong> ${data.cnn_annotations.context.prediction} 
                        <span style="font-size: 11px; color: #856404;">(${(data.cnn_annotations.context.confidence * 100).toFixed(1)}%)</span></div>`;
                }
                if (data.cnn_annotations.scene) {
                    html += `<div style="margin: 3px 0;"><strong>Scene:</strong> ${data.cnn_annotations.scene.prediction} 
                        <span style="font-size: 11px; color: #856404;">(${(data.cnn_annotations.scene.confidence * 100).toFixed(1)}%)</span></div>`;
                }
                html += '</div>';
            }
            
            infoContent.innerHTML = html;
        })
        .catch(err => {
            console.error('Error loading frame data:', err);
            infoContent.innerHTML = '<div style="color: #dc3545;">Error loading frame data</div>';
        });
}

// Handle sticky navigation and frame loading with throttling
function handleScrollEvents() {
    // Clear existing timeout
    if (scrollTimeout) {
        clearTimeout(scrollTimeout);
    }
    
    // Throttle scroll events to improve performance
    scrollTimeout = setTimeout(() => {
        // Handle sticky navigation
        handleStickyNav();
        
        // Handle infinite scroll for frame loading
        const scrollY = window.scrollY || window.pageYOffset;
        const viewport = window.innerHeight;
        const fullHeight = document.body.offsetHeight;
        
        // Load more frames when near the bottom (reduced threshold for better UX)
        if (scrollY + viewport > fullHeight - 200) {
            if (framesLoaded < allFrames.length && !loadingFrames) {
                loadNextFrames();
            }
        }
    }, 16); // ~60fps throttling
}

// Handle sticky navigation (called from throttled scroll handler)
function handleStickyNav() {
    const sessionInfo = document.getElementById('session-info');
    const scrolled = window.scrollY > 20;
    
    if (scrolled) {
        sessionInfo.classList.add('scrolled');
    } else {
        sessionInfo.classList.remove('scrolled');
    }
}
