// News 2000 - Client-side JavaScript

// Search functionality for sidebar search
const sidebarSearch = document.getElementById('sidebarSearch');
const sidebarSearchResults = document.getElementById('sidebarSearchResults');
let sidebarSearchTimeout;

if (sidebarSearch) {
    sidebarSearch.addEventListener('input', function() {
        clearTimeout(sidebarSearchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            sidebarSearchResults.style.display = 'none';
            return;
        }
        
        sidebarSearchTimeout = setTimeout(() => {
            fetch(`/search?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(response => response.json())
                .then(results => {
                    if (results.length > 0) {
                        sidebarSearchResults.innerHTML = results.map(result => `
                            <a href="/news/${encodeURIComponent(result.title)}" class="search-result-item">
                                <div class="result-title">${escapeHtml(result.title)}</div>
                                ${result.date ? `<div class="result-date">${escapeHtml(result.date)}</div>` : ''}
                            </a>
                        `).join('');
                        sidebarSearchResults.style.display = 'block';
                    } else {
                        sidebarSearchResults.innerHTML = '<div class="no-results">No results found</div>';
                        sidebarSearchResults.style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                });
        }, 300);
    });

    const sidebarSearchBtn = document.getElementById('sidebarSearchBtn');
    if (sidebarSearchBtn) {
        sidebarSearchBtn.addEventListener('click', function() {
            const query = sidebarSearch.value.trim();
            if (query) {
                window.location.href = `/search?q=${encodeURIComponent(query)}`;
            }
        });
    }
    
    // Navigate on Enter key
    sidebarSearch.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const query = this.value.trim();
            if (query) {
                window.location.href = `/search?q=${encodeURIComponent(query)}`;
            }
        }
    });
}

// Close search results when clicking outside
document.addEventListener('click', function(e) {
    if (sidebarSearch && sidebarSearchResults && 
        !sidebarSearch.contains(e.target) && 
        !sidebarSearchResults.contains(e.target) &&
        !document.getElementById('sidebarSearchBtn')?.contains(e.target)) {
        sidebarSearchResults.style.display = 'none';
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
        const href = this.getAttribute('href');
        if (href === '#top') {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        } else {
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// Console message
console.log('%c📰 News 2000 Reader', 'font-size: 24px; font-weight: bold; color: #c40000;');
console.log('%cNews 2000 style interface', 'font-size: 12px; color: #666;');

