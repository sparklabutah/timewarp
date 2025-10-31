// Simple Wikipedia UI - JavaScript

// Search functionality
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');

let searchTimeout;

if (searchInput) {
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        
        searchTimeout = setTimeout(() => {
            fetch(`/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(results => {
                    if (results.length > 0) {
                        searchResults.innerHTML = results.map(result => `
                            <a href="/wiki/${encodeURIComponent(result.title)}" class="search-result-item">
                                <div class="result-title">${escapeHtml(result.title)}</div>
                            </a>
                        `).join('');
                        searchResults.style.display = 'block';
                    } else {
                        searchResults.innerHTML = '<div class="no-results">No results found</div>';
                        searchResults.style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                    searchResults.innerHTML = '<div class="no-results">Error performing search</div>';
                    searchResults.style.display = 'block';
                });
        }, 300);
    });

    // Navigate on Enter key
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const query = this.value.trim();
            if (query) {
                window.location.href = `/wiki/${encodeURIComponent(query)}`;
            }
        }
    });
}

// Close search results when clicking outside
document.addEventListener('click', function(e) {
    if (searchInput && !searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.style.display = 'none';
    }
});

// Random article button
const randomBtn = document.getElementById('randomBtn');
if (randomBtn) {
    randomBtn.addEventListener('click', function() {
        // Navigate directly to /random route, which will redirect to a random article
        window.location.href = '/random';
    });
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Smooth scroll to top
document.querySelectorAll('a[href="#top"]').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
});

