// Global scenes lookup for the current session
window.scenesLookup = new Set();

// Initialize the lookup by fetching all scenes for the current session
function initializeScenesLookup(sessionId) {
    if (typeof fetchScenes !== 'function') {
        console.error('fetchScenes function not found.');
        return;
    }
    fetchScenes(sessionId).then(scenes => {
        window.scenesLookup = new Set(scenes);
        console.log('Scenes lookup initialized:', window.scenesLookup);
        setTimeout(updateScenesDatalist, 500);
    });
}

// Add a new scene to the lookup
function updateScenesLookup(newTag) {
    if (newTag && typeof newTag === 'string') {
        window.scenesLookup.add(newTag);
        updateScenesDatalist();
    }
}

function updateScenesDatalist() {
    const datalist = document.getElementById('scenes-datalist');
    if (!datalist || !window.scenesLookup) return;
    datalist.innerHTML = '';
    window.scenesLookup.forEach(scene => {
        const option = document.createElement('option');
        option.value = scene;
        datalist.appendChild(option);
    });
}



