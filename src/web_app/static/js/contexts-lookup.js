// Global contexts lookup for the current session
window.contextsLookup = new Set();

// Initialize the lookup by fetching all contexts for the current session
function initializeContextsLookup(sessionId) {
    if (typeof fetchContexts !== 'function') {
        console.error('fetchContexts function not found.');
        return;
    }
    fetchContexts(sessionId).then(contexts => {
        window.contextsLookup = new Set(contexts);
        console.log('Contexts lookup initialized:', window.contextsLookup);
        setTimeout(() => { 
            updateContextsDatalist()
            loadDropdownData(sessionId);
        }, 500);
    });
}

// Add a new context to the lookup
function updateContextsLookup(newContext) {
    if (newContext && typeof newContext === 'string') {
        window.contextsLookup.add(newContext);
        updateContextsDatalist();
    }
}

function updateContextsDatalist() {
    const datalist = document.getElementById('contexts-datalist');
    if (!datalist || !window.contextsLookup) return;
    datalist.innerHTML = '';
    window.contextsLookup.forEach(context => {
        const option = document.createElement('option');
        option.value = context;
        datalist.appendChild(option);
    });
}



