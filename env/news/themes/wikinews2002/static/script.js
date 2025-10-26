// Wikinews - Client-side JavaScript

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
                            <a href="/news/${encodeURIComponent(result.title)}" class="search-result-item">
                                <div class="result-title">${escapeHtml(result.title)}</div>
                                ${result.date ? `<div class="result-date">${escapeHtml(result.date)}</div>` : ''}
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
                });
        }, 300);
    });

    // Navigate on Enter key
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const query = this.value.trim();
            if (query) {
                window.location.href = `/news/${encodeURIComponent(query)}`;
            }
        }
    });
}

// Close search results when clicking outside
document.addEventListener('click', function(e) {
    if (searchInput && searchResults && 
        !searchInput.contains(e.target) && 
        !searchResults.contains(e.target)) {
        searchResults.style.display = 'none';
    }
});

// Random article button
const randomBtn = document.getElementById('randomBtn');
if (randomBtn) {
    randomBtn.addEventListener('click', function() {
        fetch('/random')
            .then(response => response.json())
            .then(data => {
                if (data.title) {
                    window.location.href = `/news/${encodeURIComponent(data.title)}`;
                } else {
                    alert('No articles available');
                }
            })
            .catch(error => {
                console.error('Random article error:', error);
            });
    });
}

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

// Add loading indicator for page navigation
let isNavigating = false;
document.addEventListener('click', function(e) {
    const link = e.target.closest('a');
    if (link && link.href && !link.target && !isNavigating) {
        const url = new URL(link.href);
        if (url.origin === window.location.origin && url.pathname !== window.location.pathname) {
            isNavigating = true;
            document.body.style.cursor = 'wait';
        }
    }
});

// Console message
console.log('%c📰 Wikinews Reader', 'font-size: 24px; font-weight: bold; color: #c40000;');
console.log('%cLocal Wikinews interface - Content from Wikimedia Foundation', 'font-size: 12px; color: #666;');

