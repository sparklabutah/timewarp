// Wikipedia 2002 Retro Theme - JavaScript

// Topbar search functionality
function performTopbarSearch() {
    const query = document.getElementById('topbarSearch').value.trim();
    if (query) {
        window.location.href = '/wiki/' + encodeURIComponent(query);
    }
    return false; // Prevent form submission
}

// Footer search functionality
function performFooterSearch() {
    const query = document.getElementById('footerSearch').value.trim();
    if (query) {
        window.location.href = '/wiki/' + encodeURIComponent(query);
    }
    return false; // Prevent form submission
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

const recentChangesSidebar = document.getElementById('recentChangesSidebar');
if (recentChangesSidebar) {
    recentChangesSidebar.addEventListener('click', function(e) {
        e.preventDefault();
        alert('Recent changes feature is not available in this offline reader.');
    });
}

// Random dropdown functionality
const randomDropdown = document.getElementById('randomDropdown');
if (randomDropdown) {
    randomDropdown.addEventListener('click', function(e) {
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

// Log page load for authentic retro feel
console.log('Wikipedia 2002 - Page loaded successfully');


