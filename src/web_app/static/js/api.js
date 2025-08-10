// Fetch all contexts for the current session
function fetchContexts(sessionId) {
    if (!sessionId) return Promise.resolve([]);
    return fetch(`/api/contexts/${sessionId}`)
        .then(res => res.ok ? res.json() : { contexts: [] })
        .then(data => data.contexts || [])
        .catch(err => {
            console.error('Error fetching contexts:', err);
            return [];
        });
}


// Fetch all scenes for the current session
function fetchScenes(sessionId) {
    if (!sessionId) return Promise.resolve([]);
    return fetch(`/api/scenes/${sessionId}`)
        .then(res => res.ok ? res.json() : { scenes: [] })
        .then(data => data.scenes || [])
        .catch(err => {
            console.error('Error fetching scenes:', err);
            return [];
    });
}

// Fetch all tags for the current session

// Fetch all actions, intents, and outcomes for the current session
function fetchActions(sessionId) {
    if (!sessionId) return Promise.resolve({ actions: [], intents: [], outcomes: [] });
    return fetch(`/api/actions/${sessionId}`)
        .then(res => res.ok ? res.json() : { actions: [], intents: [], outcomes: [] })
        .catch(err => {
            console.error('Error fetching actions:', err);
            return { actions: [], intents: [], outcomes: [] };
        });
}

function fetchTags(sessionId) {
    if (!sessionId) return Promise.resolve([]);
    return fetch(`/api/tags/${sessionId}`)
        .then(res => res.ok ? res.json() : { tags: [] })
        .then(data => data.tags || [])
        .catch(err => {
            console.error('Error fetching tags:', err);
            return [];
        });
}




// Frame Grid Annotator - API Utilities
// Session management and API communication

// Get current session ID from the select element
function getCurrentSessionId() {
    const select = document.getElementById('session-select');
    return select ? select.value : null;
}

// Build API URLs with session support
function apiUrl(endpoint, ...params) {
    const sessionId = getCurrentSessionId();
    let url = `/api/${endpoint}`;
    if (sessionId) {
        url += `/${sessionId}`;
    }
    if (params.length > 0) {
        url += `/${params.join('/')}`;
    }
    return url;
}

// Session management functions
function fetchAndStoreSessionMetadata(sessionId) {
    fetch('/api/sessions')
        .then(res => res.json())
        .then(data => {
            const currentSession = data.sessions.find(session => session.session_id === sessionId);
            if (currentSession && currentSession.metadata) {
                // Store session metadata in local storage
                localStorage.setItem('currentSessionMetadata', JSON.stringify(currentSession.metadata));
                localStorage.setItem('currentSessionId', currentSession.session_id);

                // Update global sessionMetadata object if it exists
                if (typeof sessionMetadata !== 'undefined') {
                    Object.assign(sessionMetadata, currentSession.metadata);
                    sessionMetadata.total_frame_sets = currentSession.metadata.total_frame_sets || currentSession.metadata.total_frames || 0;
                }
                
                console.log('Session metadata stored:', currentSession.metadata);
            }
        })
        .catch(err => {
            console.error('Error fetching session metadata:', err);
        });
}

function getCurrentSessionMetadata() {
    const stored = localStorage.getItem('currentSessionMetadata');
    return stored ? JSON.parse(stored) : null;
}

function refreshSessions() {
    fetch('/api/sessions')
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById('session-select');
            select.innerHTML = '<option value="">Select a session...</option>';
            
            data.sessions.forEach(session => {
                const option = document.createElement('option');
                option.value = session.session_id;
                const frameCount = session.metadata.total_frame_sets ||  0;
                localStorage.setItem('currentSessionId', session.session_id);
                localStorage.setItem('currentSessionMetadata', JSON.stringify(session.metadata));
                option.textContent = `${session.session_id} (${frameCount} frame sets)`;
                select.appendChild(option);
            });
        })
        .catch(err => {
            console.error('Error loading sessions:', err);
            const select = document.getElementById('session-select');
            select.innerHTML = '<option value="">Error loading sessions</option>';
        });
}

function showSessionInfo(sessionId) {
    if (!sessionId) {
        document.getElementById('session-info').style.display = 'none';
        return;
    }
    
    // Just show the session info div and update completion stats
    document.getElementById('session-info').style.display = 'block';
    if (typeof updateCompletionStats === 'function') {
        updateCompletionStats();
    }
}

function changeSession() {
    const sessionId = getCurrentSessionId();
    currentSessionId = sessionId;
    
    if (sessionId) {
        // Reset frame state
        selectedFrames.clear();
        selectedFramesOrder = [];
        frameOrder = [];
        lastSelectedFrame = null;
        
        // Reset filter to 'all' when changing sessions
        const filterSelect = document.getElementById('frame-filter');
        if (filterSelect) {
            filterSelect.value = 'all';
            if (typeof currentFilter !== 'undefined') {
                currentFilter = 'all';
            }
        }
        
        // Remove all frame-item elements from the grid to ensure no leftover frames persist
        const frameGrid = document.getElementById('frame-grid');
        while (frameGrid.firstChild) {
            frameGrid.removeChild(frameGrid.firstChild);
        }
        
        // Fetch and store session metadata, then continue session setup
        fetch('/api/sessions')
            .then(res => res.json())
            .then(data => {
                const currentSession = data.sessions.find(session => session.session_id === sessionId);
                if (currentSession && currentSession.metadata) {
                    localStorage.setItem('currentSessionMetadata', JSON.stringify(currentSession.metadata));
                    localStorage.setItem('currentSessionId', currentSession.session_id);
                    if (typeof sessionMetadata !== 'undefined') {
                        Object.assign(sessionMetadata, currentSession.metadata);
                        sessionMetadata.total_frame_sets = currentSession.metadata.total_frame_sets || currentSession.metadata.total_frames || 0;
                    }
                    console.log('Session metadata stored:', currentSession.metadata);
                }
                // Now continue with session setup
                showSessionInfo(sessionId);
                document.getElementById('session-info').style.display = 'block';
                initializeRecentButtons();
                fetchSessionProgress();
                loadFrames(currentFilter || 'all');
                updateBulkAnnotateButton();
                updateSidebar();
                initializeContextsLookup(sessionId);
                initializeTagsLookup(sessionId);
                initializeScenesLookup(sessionId);
                initializeActionsLookup(sessionId);
            })
            .catch(err => {
                console.error('Error fetching session metadata:', err);
            });
    } else {
        // Clear session metadata when no session is selected
        localStorage.removeItem('currentSessionMetadata');
        document.getElementById('session-info').style.display = 'none';
        document.getElementById('frame-grid').innerHTML = '';
    }
}


