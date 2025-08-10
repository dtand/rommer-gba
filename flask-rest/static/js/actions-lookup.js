// Global action-related lookups for the current session
window.actionsLookup = [];
window.intentsLookup = [];
window.outcomesLookup = [];

// Initialize the lookups by fetching all actions for the current session
function initializeActionsLookup(sessionId) {
    if (typeof fetchActions !== 'function') {
        console.error('fetchActions function not found.');
        return;
    }
    fetchActions(sessionId).then(data => {
        window.actionsLookup = Array.isArray(data.actions) ? data.actions.slice().sort() : [];
        window.intentsLookup = Array.isArray(data.intents) ? data.intents.slice().sort() : [];
        window.outcomesLookup = Array.isArray(data.outcomes) ? data.outcomes.slice().sort() : [];
        console.log('Actions lookup initialized:', window.actionsLookup);
        console.log('Intents lookup initialized:', window.intentsLookup);
        console.log('Outcomes lookup initialized:', window.outcomesLookup);
        setTimeout(() => {
            updateActionsDatalist();
            updateIntentsDatalist();
            updateOutcomesDatalist();
            loadDropdownData(sessionId);
        }, 500);
        
    });
}

// Add a new action to the lookup
function updateActionsLookup(newAction) {
    if (newAction && typeof newAction === 'string' && !window.actionsLookup.includes(newAction)) {
        window.actionsLookup.push(newAction);
        window.actionsLookup.sort();
        updateActionsDatalist();
    }
}

function updateActionsDatalist() {
    const datalist = document.getElementById('actions-datalist');
    if (!datalist || !window.actionsLookup) return;
    datalist.innerHTML = '';
    window.actionsLookup.forEach(action => {
        const option = document.createElement('option');
        option.value = action;
        datalist.appendChild(option);
    });
}

// Add a new intent to the lookup
function updateIntentsLookup(newIntent) {
    if (newIntent && typeof newIntent === 'string' && !window.intentsLookup.includes(newIntent)) {
        window.intentsLookup.push(newIntent);
        window.intentsLookup.sort();
        updateIntentsDatalist();
    }
}

function updateIntentsDatalist() {
    const datalist = document.getElementById('intents-datalist');
    if (!datalist || !window.intentsLookup) return;
    datalist.innerHTML = '';
    window.intentsLookup.forEach(intent => {
        const option = document.createElement('option');
        option.value = intent;
        datalist.appendChild(option);
    });
}

// Add a new outcome to the lookup
function updateOutcomesLookup(newOutcome) {
    if (newOutcome && typeof newOutcome === 'string' && !window.outcomesLookup.includes(newOutcome)) {
        window.outcomesLookup.push(newOutcome);
        window.outcomesLookup.sort();
        updateOutcomesDatalist();
    }
}

function updateOutcomesDatalist() {
    const datalist = document.getElementById('outcomes-datalist');
    if (!datalist || !window.outcomesLookup) return;
    datalist.innerHTML = '';
    window.outcomesLookup.forEach(outcome => {
        const option = document.createElement('option');
        option.value = outcome;
        datalist.appendChild(option);
    });
}



