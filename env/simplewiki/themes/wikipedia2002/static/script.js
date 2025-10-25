// Wikipedia 2002 Retro Theme - JavaScript

// Main search functionality
function performSearch() {
    const query = document.getElementById('mainSearch').value.trim();
    if (query) {
        window.location.href = '/wiki/' + encodeURIComponent(query);
    }
}

function performSidebarSearch() {
    const query = document.getElementById('sidebarSearch').value.trim();
    if (query) {
        window.location.href = '/wiki/' + encodeURIComponent(query);
    }
}

// Enter key support for main search
const mainSearch = document.getElementById('mainSearch');
if (mainSearch) {
    mainSearch.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

// Enter key support for sidebar search
const sidebarSearch = document.getElementById('sidebarSearch');
if (sidebarSearch) {
    sidebarSearch.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSidebarSearch();
        }
    });
}

// Random page functionality
const randomPage = document.getElementById('randomPage');
if (randomPage) {
    randomPage.addEventListener('click', function(e) {
        e.preventDefault();
        fetch('/random')
            .then(response => response.json())
            .then(data => {
                if (data.title) {
                    window.location.href = '/wiki/' + encodeURIComponent(data.title);
                }
            })
            .catch(error => {
                console.error('Random article error:', error);
                alert('Could not load random article');
            });
    });
}

// Sidebar random page
const randomSidebar = document.getElementById('randomSidebar');
if (randomSidebar) {
    randomSidebar.addEventListener('click', function(e) {
        e.preventDefault();
        fetch('/random')
            .then(response => response.json())
            .then(data => {
                if (data.title) {
                    window.location.href = '/wiki/' + encodeURIComponent(data.title);
                }
            })
            .catch(error => {
                console.error('Random article error:', error);
            });
    });
}

// Recent changes (dummy functionality for retro feel)
const recentChanges = document.getElementById('recentChanges');
if (recentChanges) {
    recentChanges.addEventListener('click', function(e) {
        e.preventDefault();
        alert('Recent changes feature is not available in this offline reader.');
    });
}

// Log page load for authentic retro feel
console.log('Wikipedia 2002 - Page loaded successfully');


