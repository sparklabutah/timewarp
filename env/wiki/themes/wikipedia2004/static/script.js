/**
 * Wikipedia 2004 Theme JavaScript
 * Handles search, navigation, and other interactive features
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    initSearch();
    
    // Initialize navigation links
    initNavigation();
    
    // Show site subtitle
    const siteSub = document.getElementById('siteSub');
    if (siteSub) {
        siteSub.style.display = 'block';
    }
});

/**
 * Initialize search functionality
 */
function initSearch() {
    const searchForms = document.querySelectorAll('#searchform, form[action="/"]');
    
    searchForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const searchInput = this.querySelector('input[name="search"]');
            if (searchInput && searchInput.value.trim()) {
                performSearch(searchInput.value.trim());
            }
            
            return false;
        });
    });
    
    // Add search input autocomplete
    const searchInputs = document.querySelectorAll('#topSearch, #searchInput, input[name="search"]');
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            if (this.value.length >= 2) {
                fetchSearchSuggestions(this.value);
            }
        }, 300));
    });
}

/**
 * Perform search and navigate to results
 */
function performSearch(query) {
    // Navigate directly to the article page or index with search parameter
    // This will show the 404 page if the article doesn't exist
    window.location.href = `/wiki/${encodeURIComponent(query)}`;
}

/**
 * Fetch search suggestions (for autocomplete)
 */
function fetchSearchSuggestions(query) {
    fetch(`/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            // Here you could implement autocomplete dropdown
            // For now, we'll just log the suggestions
            console.log('Search suggestions:', data);
        })
        .catch(error => {
            console.error('Error fetching suggestions:', error);
        });
}

/**
 * Initialize navigation links
 */
function initNavigation() {
    // Random page links
    const randomLinks = document.querySelectorAll('#randomPage, #randomSidebar, #randomLink, #randomDropdown');
    randomLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            getRandomArticle();
        });
    });
    
    // Recent changes links
    const recentChangesLinks = document.querySelectorAll('#recentChanges, #recentChangesSidebar');
    recentChangesLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            alert('Recent changes feature is not available in this demo.');
        });
    });
}

/**
 * Get and navigate to a random article
 */
function getRandomArticle() {
    // Navigate directly to /random route, which will redirect to a random article
    window.location.href = '/random';
}

/**
 * Debounce function to limit API calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Handle topbar search
 */
function performTopbarSearch() {
    const searchInput = document.getElementById('topbarSearch');
    if (searchInput && searchInput.value.trim()) {
        performSearch(searchInput.value.trim());
    }
    return false;
}

/**
 * Handle footer search
 */
function performFooterSearch() {
    const searchInput = document.getElementById('footerSearch');
    if (searchInput && searchInput.value.trim()) {
        performSearch(searchInput.value.trim());
    }
    return false;
}

// Make functions available globally for inline handlers
window.performTopbarSearch = performTopbarSearch;
window.performFooterSearch = performFooterSearch;

