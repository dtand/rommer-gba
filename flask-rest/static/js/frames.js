let sessionProgress = {
    complete_count: 0,
    partially_complete_count: 0,
    total_count: 0,
};


// Update bulk annotate button state
function updateBulkAnnotateButton() {
    const annotateButton = document.getElementById('bulk-annotate-btn');
    const completeButton = document.getElementById('bulk-complete-btn');
    const hasSelection = selectedFramesOrder.length > 0;
    
    annotateButton.disabled = !hasSelection;
    annotateButton.title = hasSelection 
        ? `Bulk annotate ${selectedFramesOrder.length} selected frame(s)`
        : 'Select frames to enable bulk annotation';
        
    completeButton.disabled = !hasSelection;
    completeButton.title = hasSelection 
        ? `Mark ${selectedFramesOrder.length} selected frame(s) as complete`
        : 'Select frames to enable marking as complete';
}

// Frame selection and interaction
function toggleFrame(frameNumber, event) {
    const frameElement = document.getElementById('frame-' + frameNumber);
    
    if (event && event.shiftKey && lastSelectedFrame !== null) {
        // Range selection
        selectFrameRange(lastSelectedFrame, frameNumber);
        return;
    }
    
    if (selectedFrames.has(frameNumber)) {
        // Deselect frame
        selectedFrames.delete(frameNumber);
        frameElement.classList.remove('selected');
        
        // Remove from ordered selection
        const index = selectedFramesOrder.indexOf(frameNumber);
        if (index > -1) {
            selectedFramesOrder.splice(index, 1);
        }
        
        // Update last selected frame
        if (selectedFramesOrder.length > 0) {
            lastSelectedFrame = selectedFramesOrder[selectedFramesOrder.length - 1];
        } else {
            lastSelectedFrame = null;
        }
    } else {
        // Select frame
        selectedFrames.add(frameNumber);
        frameElement.classList.add('selected');
        selectedFramesOrder.push(frameNumber);
        lastSelectedFrame = frameNumber;
    }
    
    updateSidebar();
    updateBulkAnnotateButton();
}

function selectFrameRange(startFrame, endFrame) {
    // Determine the actual range based on frame order in the grid
    const start = frameOrder.indexOf(startFrame);
    const end = frameOrder.indexOf(endFrame);
    
    if (start === -1 || end === -1) return;
    
    const min = Math.min(start, end);
    const max = Math.max(start, end);
    
    // Select all frames in the range
    for (let i = min; i <= max; i++) {
        const frameNumber = frameOrder[i];
        if (!selectedFrames.has(frameNumber)) {
            selectedFrames.add(frameNumber);
            selectedFramesOrder.push(frameNumber);
            const frameElement = document.getElementById('frame-' + frameNumber);
            if (frameElement) {
                frameElement.classList.add('selected');
            }
        }
    }
    
    lastSelectedFrame = endFrame;
    updateSidebar();
    updateBulkAnnotateButton();
}

// Frame loading functions
// Frame loading with pagination
let allFrames = [];
let filteredFrames = []; // Frames after applying filter
let currentFilter = 'all'; // Current filter state
let loadedFrameCount = 0;
let firstLoadedFrameIndex = 0;  // Track the first loaded frame index
const FRAMES_PER_LOAD = 50; // Load 50 frames at a time
let isLoading = false;

// Get starting frame position based on last annotated frame
function getStartingFramePosition() {
    const lastAnnotatedFrame = localStorage.getItem('lastAnnotatedFrame');
    if (!lastAnnotatedFrame) return 0;
    
    const frameNumber = parseInt(lastAnnotatedFrame);
    const frameIndex = filteredFrames.findIndex(f => f.frame === frameNumber);
    
    if (frameIndex === -1) return 0;
    
    // Start a bit before the last annotated frame (10 frames back)
    const startIndex = Math.max(0, frameIndex - 10);
    return startIndex;
}

function loadFrames(filter = 'all', forceReload = false) {
    
    currentFilter = filter;
    console.log(`DEBUG: loadFrames called with currentFilter: ${currentFilter}, forceReload: ${forceReload}`);
    window.scrollTo({ top: 0, behavior: 'auto' });
    grid = document.getElementById('frame-grid');
    grid.scrollTop = 0;

    if (!getCurrentSessionId()) return;
    // Reset lastSelectedFrame when loading new frames (e.g., after session change)
    lastSelectedFrame = null;
    // Always fetch from API when filter changes or forced reload
    if (forceReload || allFrames.length === 0) {
        // Build API URL with filter parameter
        let url = apiUrl('frames');
        if (currentFilter !== 'all') {
            url += `?filter=${currentFilter}`;
        }
        
        console.log(`DEBUG: Loading frames with URL: ${url}`);  // Debug logging
        
        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('frame-grid').innerHTML = `<p>Error: ${data.error}</p>`;
                    return;
                }
                
                allFrames = data.frames;
                filteredFrames = [...allFrames]; // Backend already filtered, so set both arrays
                frameOrder = allFrames.map(f => f.frame);
                
                console.log(`DEBUG: Loaded ${data.total_filtered} frames with filter: ${data.filter}`);
                localStorage.setItem('lastAnnotatedFrame', allFrames[0].frame);
                // Start from last annotated position or beginning
                const startingPosition = getStartingFramePosition();
                loadedFrameCount = startingPosition;
                firstLoadedFrameIndex = startingPosition;
                
                const grid = document.getElementById('frame-grid');
                grid.innerHTML = '';
                
                // Load initial batch of frames from starting position
                loadNextFrameBatch();
                
                updateCompletionStats();
                
                // Scroll to the appropriate position after a short delay
                setTimeout(() => {
                    const lastAnnotatedFrame = localStorage.getItem('lastAnnotatedFrame');
                    if (lastAnnotatedFrame) {
                        const frameElement = document.getElementById('frame-' + lastAnnotatedFrame);
                        if (frameElement) {
                            frameElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }
                }, 500);
            })
            .catch(err => {
                console.error('Error loading frames:', err);
                document.getElementById('frame-grid').innerHTML = '<p>Error loading frames</p>';
            });
    } else {
        // Use cached data if available and no filter change
        console.log(`DEBUG: Using cached frames, count: ${allFrames.length}`);
        
        // Start from last annotated position or beginning
        const startingPosition = getStartingFramePosition();
        loadedFrameCount = startingPosition;
        firstLoadedFrameIndex = startingPosition;
        
        const grid = document.getElementById('frame-grid');
        grid.innerHTML = '';
        
        // Load initial batch of frames from starting position
        loadNextFrameBatch();
        
        updateCompletionStats();
    }
}

function loadNextFrameBatch() {
    if (isLoading || loadedFrameCount >= filteredFrames.length) return;
    
    isLoading = true;
    const grid = document.getElementById('frame-grid');
    
    const endIndex = Math.min(loadedFrameCount + FRAMES_PER_LOAD, filteredFrames.length);
    const framesToLoad = filteredFrames.slice(loadedFrameCount, endIndex);
    
    framesToLoad.forEach(frame => {
        const frameDiv = createFrameElement(frame);
        grid.appendChild(frameDiv);
        
        // Mark as annotated (complete) if it has complete annotation data
        if (frame.annotated) {
            frameDiv.classList.add('annotated');
        }
        // Mark as partial if it has some annotation data but not complete
        else if (frame.partial) {
            frameDiv.classList.add('partial');
        }
    });
    
    loadedFrameCount = endIndex;
    isLoading = false;
    
    // Show loading indicator if there are more frames to load
    if (loadedFrameCount < filteredFrames.length) {
        showLoadingIndicator();
    } else {
        hideLoadingIndicator();
    }
}

// Load previous frames when scrolling up
function loadPreviousFrameBatch() {
    if (isLoading || firstLoadedFrameIndex <= 0) return;
    
    isLoading = true;
    const grid = document.getElementById('frame-grid');
    
    const startIndex = Math.max(0, firstLoadedFrameIndex - FRAMES_PER_LOAD);
    const framesToLoad = filteredFrames.slice(startIndex, firstLoadedFrameIndex);
    
    // Store current scroll position
    const currentScrollY = window.scrollY;
    
    // Insert frames at the beginning
    framesToLoad.reverse().forEach(frame => {
        const frameDiv = createFrameElement(frame);
        grid.insertBefore(frameDiv, grid.firstChild);
        
        // Mark as annotated (complete) if it has complete annotation data
        if (frame.annotated) {
            frameDiv.classList.add('annotated');
        }
        // Mark as partial if it has some annotation data but not complete
        else if (frame.partial) {
            frameDiv.classList.add('partial');
        }
    });
    
    firstLoadedFrameIndex = startIndex;
    isLoading = false;
    
    // Restore scroll position to account for new content at top
    window.scrollTo(0, currentScrollY + (framesToLoad.length * 120)); // Approximate frame height
}

function showLoadingIndicator() {
    // Indicator disabled - no longer showing loading text or element
    return;
}

function hideLoadingIndicator() {
    const indicator = document.getElementById('load-more-indicator');
    if (indicator) {
        indicator.remove();
    }
}

function createFrameElement(frame) {
    const frameDiv = document.createElement('div');
    frameDiv.className = 'frame-item';
    frameDiv.id = 'frame-' + frame.frame;
    frameDiv.onclick = (e) => toggleFrame(frame.frame, e);
    
    // Add hover event handlers
    frameDiv.onmouseenter = () => {
        currentHoveredFrame = frame.frame;
        frameDiv.classList.add('hovered');
        updateSidebar(frame.frame);
    };
    
    frameDiv.onmouseleave = () => {
        currentHoveredFrame = null;
        frameDiv.classList.remove('hovered');
        // Update sidebar to show selected frames or clear
        if (selectedFramesOrder.length > 0) {
            updateSidebar(selectedFramesOrder[selectedFramesOrder.length - 1], true);
        } else {
            updateSidebar();
        }
    };
    
    const img = document.createElement('img');
    img.src = apiUrl('frame_image', frame.frame);
    img.alt = `Frame ${frame.frame}`;
    
    const label = document.createElement('p');
    label.textContent = `Frame ${frame.frame}`;
    
    frameDiv.appendChild(img);
    frameDiv.appendChild(label);
    
    return frameDiv;
}

// Handle scroll events for loading more frames and sticky navigation
function handleScrollEvents() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

    
    // Check if we need to load more frames (when user is near bottom)
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
        loadNextFrameBatch();
    }
    
    // Check if we need to load previous frames (when user is near top)
    if (scrollTop < 500 && firstLoadedFrameIndex > 0) {
        loadPreviousFrameBatch();
    }
    
    // Handle sticky navigation
    const sessionInfo = document.getElementById('session-info');
    sessionInfo.style.top = '0px'; // Always stick to the top
}

// Fetch session-level progress from backend
function fetchSessionProgress() {
    const sessionId = getCurrentSessionId();
    if (!sessionId) return;
    
    const url = apiUrl('progress');
    console.log('Fetching session progress from:', url);
    
    fetch(url)
        .then(res => {
            console.log('Progress response status:', res.status);
            return res.ok ? res.json() : null;
        })
        .then(data => {
            console.log('Progress data received:', data);
            if (data) {
                sessionProgress.complete_count = data.complete;
                sessionProgress.partially_complete_count = data.partial;
                sessionProgress.total_count = data.total;
                displayProgressStats();
            }
        })
        .catch(err => {
            console.error('Error fetching session progress:', err);
            // Fallback to local calculation if API fails
            updateCompletionStats();
        });
}

// Update progress counts locally (for immediate UI feedback)
function updateLocalProgress(isComplete, wasComplete = false, hadAnnotation = false) {
    if (isComplete && !wasComplete) {
        // Frame became complete
        sessionProgress.complete_count++;
        if (hadAnnotation) {
            // Was partially complete, now complete
            sessionProgress.partially_complete_count--;
        }
    } else if (!isComplete && wasComplete) {
        // Frame was unmarked from complete
        sessionProgress.complete_count--;
        // Check if it still has annotations (becomes partial)
        // This would need additional logic to check actual annotation state
    } else if (!isComplete && !wasComplete && !hadAnnotation) {
        // Frame got its first annotation (became partial)
        sessionProgress.partially_complete_count++;
    }
    
    // Recalculate percentage
    sessionProgress.progress_percentage = sessionProgress.total_count > 0 ? 
        (sessionProgress.complete_count / sessionProgress.total_count * 100) : 0;
    
    displayProgressStats();
}

// Generate progress statistics HTML (single source of truth)
function generateProgressStatsHTML() {
    // Get session metadata from localStorage or global variable
    const storedMetadata = localStorage.getItem('currentSessionMetadata');
    const metadata = storedMetadata ? JSON.parse(storedMetadata) : sessionMetadata;
    
    // Calculate completion rate based on completed frames / total session frames
    const totalSessionFrames = metadata.total_frame_sets || 1;
    const completionRate = totalSessionFrames > 0 ? ((sessionProgress.complete_count / totalSessionFrames) * 100).toFixed(1) : 0;

    return `
        <div style="display: flex; align-items: center; gap: 12px; width: 100%;">
            <span class="stats-item"><b>${metadata.game_name || 'Unknown Game'}</b></span>
            <span class="stats-item">✅ Complete: <span class="stats-number" style="color: #28a745;">${sessionProgress.complete_count}</span></span>
            <span class="stats-item">🟡 Partial: <span class="stats-number" style="color: #fd7e14;">${sessionProgress.partially_complete_count}</span></span>
            <span class="stats-item">Completion Rate: <span class="completion-rate">${completionRate}%</span></span>
            <div class="progress-bar-container" style="flex: 1; height: 16px; background: #e9ecef; border: 1px solid #ced4da; border-radius: 10px; overflow: hidden;">
                <div class="progress-bar" style="width: ${completionRate}%; height: 100%; background: linear-gradient(90deg, #28a745, #20c997); transition: width 0.3s ease;"></div>
            </div>
        </div>
    `;
}

// Display progress statistics (used by both session data and local updates)
function displayProgressStats() {
    const existingStats = document.querySelector('.session-stats');
    if (existingStats) {
        existingStats.remove();
    }
    
    const sessionId = getCurrentSessionId();
    if (!sessionId) return;
    
    const sessionInfo = document.getElementById('session-info');
    const statsDiv = document.createElement('div');
    statsDiv.className = 'session-stats';
    statsDiv.innerHTML = generateProgressStatsHTML(sessionProgress);
    
    sessionInfo.appendChild(statsDiv);
}

// Fallback completion stats (for when session progress is not available)
function updateCompletionStats() {
    // If we have session progress data, use the main display function
    if (sessionProgress.complete_count > 0 || sessionProgress.partially_complete_count > 0) {
        displayProgressStats();
        return;
    }
    
    // Fallback to calculating from loaded frames only
    if (!getCurrentSessionId()) return;
    
    const frameElements = document.querySelectorAll('.frame-item');
    const totalFrames = frameElements.length;
    const completedFrames = document.querySelectorAll('.frame-item.annotated').length;
    const partialFrames = document.querySelectorAll('.frame-item.partial').length;
    const unAnnotatedFrames = totalFrames - completedFrames - partialFrames;
    
    const existingStats = document.querySelector('.session-stats');
    if (existingStats) {
        existingStats.remove();
    }
    
    const sessionInfo = document.getElementById('session-info');
    const statsDiv = document.createElement('div');
    statsDiv.className = 'session-stats';
    
    const completionRate = totalFrames > 0 ? ((completedFrames / totalFrames) * 100).toFixed(1) : 0;
    
    statsDiv.innerHTML = generateProgressStatsHTML();
    
    sessionInfo.appendChild(statsDiv);
}

function markFrameAsAnnotated(frameId) {
    const frameDiv = document.getElementById('frame-' + frameId);
    if (frameDiv) {
        const wasPartial = frameDiv.classList.contains('partial');
        const wasAnnotated = frameDiv.classList.contains('annotated');
        
        // Remove partial class and add annotated class (frame is now complete)
        frameDiv.classList.remove('partial');
        frameDiv.classList.add('annotated');
        
        // Update local progress tracking
        updateLocalProgress(true, wasAnnotated, wasPartial);
        
        // Track last annotated frame for sidebar fallback
        lastAnnotatedFrame = frameId;
        
        // Update sidebar if no current hover or selection
        if (!currentHoveredFrame && selectedFramesOrder.length === 0) {
            updateSidebar(frameId, false, true);
        }
    }
}

function markFrameAsPartial(frameId) {
    const frameDiv = document.getElementById('frame-' + frameId);
    if (frameDiv) {
        const wasAnnotated = frameDiv.classList.contains('annotated');
        const wasPartial = frameDiv.classList.contains('partial');
        
        // Remove annotated class and add partial class
        frameDiv.classList.remove('annotated');
        frameDiv.classList.add('partial');
        
        // Update local progress tracking
        updateLocalProgress(false, wasAnnotated, wasPartial);
    }
}

// Toggle visibility of annotated frames
let annotatedFramesHidden = false;
function toggleAnnotatedFrames() {
    const annotatedFrames = document.querySelectorAll('.frame-item.annotated');
    annotatedFramesHidden = !annotatedFramesHidden;
    
    annotatedFrames.forEach(frame => {
        frame.style.display = annotatedFramesHidden ? 'none' : 'block';
    });
    
    const toggleButton = document.getElementById('toggle-annotated-btn');
    if (toggleButton) {
        toggleButton.textContent = annotatedFramesHidden ? 'Show Annotated' : 'Hide Annotated';
    }
}
