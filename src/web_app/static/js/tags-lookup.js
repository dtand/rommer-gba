// Global tags lookup for the current session
window.tagsLookup = new Set();

// Initialize the lookup by fetching all tags for the current session
function initializeTagsLookup(sessionId) {
    if (typeof fetchTags !== 'function') {
        console.error('fetchTags function not found.');
        return;
    }
    fetchTags(sessionId).then(tags => {
        window.tagsLookup = new Set(tags);
        console.log('Tags lookup initialized:', window.tagsLookup);
        setTimeout(updateTagsDatalist, 500);
    });
}

// Add a new tag to the lookup
function updateTagsLookup(newTag) {
    if (newTag && typeof newTag === 'string') {
        window.tagsLookup.add(newTag);
        updateTagsDatalist();
    }
}


function updateTagsDatalist() {
    const datalist = document.getElementById('tags-datalist');
    if (!datalist || !window.tagsLookup) return;
    datalist.innerHTML = '';
    window.tagsLookup.forEach(tag => {
        const option = document.createElement('option');
        option.value = tag;
        datalist.appendChild(option);
    });
}



