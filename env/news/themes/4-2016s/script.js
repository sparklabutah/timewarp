// News 2016 - Client-side JavaScript

// Search functionality
const searchInput = document.getElementById('searchInput');
const searchInputExpanded = document.getElementById('searchInputExpanded');
const searchResults = document.getElementById('searchResults');
const searchContainerExpanded = document.getElementById('searchContainerExpanded');
const searchIcon = document.querySelector('.search-icon');
let searchTimeout;

// Toggle search container
if (searchIcon) {
    searchIcon.addEventListener('click', function() {
        if (searchContainerExpanded) {
            const isVisible = searchContainerExpanded.style.display !== 'none';
            searchContainerExpanded.style.display = isVisible ? 'none' : 'block';
            if (!isVisible && searchInputExpanded) {
                searchInputExpanded.focus();
            }
        }
    });
}

function setupSearch(inputElement, resultsElement) {
    if (!inputElement || !resultsElement) return;
    
    inputElement.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            resultsElement.style.display = 'none';
            return;
        }
        
        searchTimeout = setTimeout(() => {
            fetch(`/search?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Search request failed');
                    }
                    return response.json();
                })
                .then(results => {
                    if (results && results.length > 0) {
                        resultsElement.innerHTML = results.map(result => `
                            <a href="/news/${encodeURIComponent(result.title)}" class="search-result-item">
                                <div class="result-title">${escapeHtml(result.title)}</div>
                                ${result.date ? `<div class="result-date">${escapeHtml(result.date)}</div>` : ''}
                            </a>
                        `).join('');
                        resultsElement.style.display = 'block';
                    } else {
                        resultsElement.innerHTML = '<div class="no-results">No results found</div>';
                        resultsElement.style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                    resultsElement.innerHTML = '<div class="no-results">Search error occurred</div>';
                    resultsElement.style.display = 'block';
                });
        }, 300);
    });

    // Navigate on Enter key - go to search results page
    inputElement.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const query = this.value.trim();
            if (query) {
                window.location.href = `/search?q=${encodeURIComponent(query)}`;
            }
        }
    });
}

// Setup both search inputs
setupSearch(searchInput, searchResults);
setupSearch(searchInputExpanded, searchResults);

// Close search results when clicking outside
document.addEventListener('click', function(e) {
    if (searchResults && 
        !searchInput?.contains(e.target) && 
        !searchInputExpanded?.contains(e.target) &&
        !searchResults.contains(e.target) &&
        !searchIcon?.contains(e.target)) {
        searchResults.style.display = 'none';
    }
});

// Utility function to escape HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Console message
console.log('%c📰 News 2016', 'font-size: 24px; font-weight: bold; color: #bb1919;');
console.log('%cBBC News 2016 style interface - Content from Wikimedia Foundation', 'font-size: 12px; color: #666;');




