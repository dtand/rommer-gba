// Frame Grid Annotator - Main Application
// Global variables and application initialization

// Frame selection and tracking
let selectedFrames = new Set();
let lastSelectedFrame = null;
let selectedFramesOrder = []; // Track selection order
let frameOrder = [];
let framesWithContext = [];
let framesLoaded = 0;
const FRAMES_PER_BATCH = 25;
let loadingFrames = false;

// Session and mode tracking
let currentSessionId = null;
let isBulkMode = false;
let currentHoveredFrame = null;
let lastAnnotatedFrame = null; // Track last annotated frame for fallback display

// Input history for modal form fields
let inputHistory = {
    context: [],
    scene: [],
    tags: [],
    description: [],
    action_type: [],
    intent: [],
    outcome: []
};

let currentHistoryIndex = {
    context: -1,
    scene: -1,
    tags: -1,
    description: -1,
    action_type: -1,
    intent: -1,
    outcome: -1
};

// Copied annotation data
let copiedAnnotation = null;

// Annotation configuration
let annotationConfig = null;

// Modal variables
let popupDiv = null;
let previewDiv = null;

function initLookups(currentSessionId) {
    // Initialize global lookups
    initializeContextsLookup(currentSessionId);
    initializeTagsLookup(currentSessionId); // Initialize tags lookup
    initializeScenesLookup(currentSessionId); // Initialize scenes lookup
    initializeActionsLookup(currentSessionId); // Initialize actions lookup
}

// Application initialization
function initializeApp() {
    currentSessionId = getCurrentSessionId();
    loadInputHistory(); // Load input history from localStorage
    initializeRecentButtons(); // Initialize recent buttons
    refreshSessions();
    setupFormSubmission(); // Set up form submission handler
    if(currentSessionId) {
        // Clear frame grid and remove all frame-item classes to prevent leftover borders
        const grid = document.getElementById('frame-grid');
        if (grid) {
            grid.innerHTML = '';
        }
        // Remove all frame-item classes from previous session
        document.querySelectorAll('.frame-item').forEach(el => {
            el.classList.remove('annotated', 'partial', 'selected', 'hovered');
        });
        initLookups(currentSessionId); // Initialize all lookups
        loadDropdownData(currentSessionId); // Load config before other operations
    }
    // Set up scroll handler
    window.addEventListener('scroll', handleScrollEvents, { passive: true });
    
    // Handle initial session ID from URL
    if (window.initialSessionId) {
        // Wait for sessions to load, then select the initial session
        setTimeout(() => {
            const select = document.getElementById('session-select');
            if (select) {
                select.value = window.initialSessionId;
                changeSession();
            }
        }, 500); // Give time for sessions to load
    }
    
    // Set up keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
            if (selectedFramesOrder.length > 0) {
                openModal();
                e.preventDefault();
            }
        }
    });
}
