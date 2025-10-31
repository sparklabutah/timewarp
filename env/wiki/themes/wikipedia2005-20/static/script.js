/**
 * Wikipedia 2005-20 Vector Theme JavaScript
 * Handles search, navigation, and other interactive features
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    initSearch();
    
    // Initialize navigation links
    initNavigation();

    // Initialize collapsible sidebar portals
    initSidebarPortals();
});

/**
 * Initialize search functionality
 */
function initSearch() {
    const searchForms = document.querySelectorAll('#p-search form, form[action="/"]');
    
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
    const searchInputs = document.querySelectorAll('#searchInput, input[name="search"]');
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
    // Random page links - find all links with href containing "random"
    const randomLinks = document.querySelectorAll('a[href="/random"], a[href*="random"]');
    randomLinks.forEach(link => {
        if (!link.getAttribute('data-initialized')) {
            link.setAttribute('data-initialized', 'true');
            link.addEventListener('click', function(e) {
                e.preventDefault();
                getRandomArticle();
            });
        }
    });
    
    // Recent changes links - do nothing (cosmetic only)
    const recentChangesLinks = document.querySelectorAll('a[href*="Recent"], a[href*="recent"]');
    recentChangesLinks.forEach(link => {
        if (!link.getAttribute('data-initialized')) {
            link.setAttribute('data-initialized', 'true');
            link.addEventListener('click', function(e) {
                e.preventDefault();
                // Cosmetic link - no action
            });
        }
    });
}

/**
 * Make left sidebar portals (Interaction/Toolbox/Print/Language) collapsible
 */
function initSidebarPortals() {
    const portals = document.querySelectorAll('#mw-panel .portal');
    portals.forEach(portal => {
        const header = portal.querySelector('h3');
        const body = portal.querySelector('.body');
        if (!header || !body) return;

        // Pointer cursor and accessibility
        header.style.cursor = 'pointer';
        header.setAttribute('role', 'button');
        header.setAttribute('tabindex', '0');

        // Restore saved state if present
        const portalId = portal.id || header.textContent.trim();
        const saved = localStorage.getItem('portal-collapsed:' + portalId);
        if (saved === 'true') {
            portal.classList.add('collapsed');
            body.style.display = 'none';
        }

        const toggle = () => {
            const isHidden = body.style.display === 'none';
            body.style.display = isHidden ? 'block' : 'none';
            portal.classList.toggle('collapsed', !isHidden);
            localStorage.setItem('portal-collapsed:' + portalId, !isHidden);
        };

        header.addEventListener('click', toggle);
        header.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggle();
            }
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
 * Toggle collapsible sections (for mobile or advanced features)
 */
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = section.style.display === 'none' ? 'block' : 'none';
    }
}

// Make functions available globally for inline handlers
window.performSearch = performSearch;
window.toggleSection = toggleSection;
