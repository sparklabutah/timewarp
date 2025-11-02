// Modern Theme JavaScript - WikiReader

// Theme Toggle
const themeToggle = document.getElementById('themeToggle');
const htmlElement = document.documentElement;
const themeIcon = document.querySelector('.theme-icon');

// Load saved theme
const savedTheme = localStorage.getItem('theme') || 'dark';
htmlElement.setAttribute('data-theme', savedTheme);
updateThemeIcon(savedTheme);

themeToggle.addEventListener('click', () => {
    const currentTheme = htmlElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    htmlElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
});

function updateThemeIcon(theme) {
    themeIcon.textContent = theme === 'dark' ? '🌙' : '☀️';
}

// Mobile Menu Toggle
const mobileMenuToggle = document.getElementById('mobileMenuToggle');
const sidebar = document.getElementById('sidebar');

if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('active');
    });

    // Close sidebar when clicking outside
    document.addEventListener('click', (e) => {
        if (!sidebar.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
            sidebar.classList.remove('active');
        }
    });
}

// Sidebar Search
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
            fetch(`/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(results => {
                    if (results.length > 0) {
                        sidebarSearchResults.innerHTML = results.map(result => `
                            <a href="/wiki/${encodeURIComponent(result.title)}">
                                ${escapeHtml(result.title)}
                            </a>
                        `).join('');
                        sidebarSearchResults.style.display = 'block';
                    } else {
                        sidebarSearchResults.innerHTML = '<div style="padding: 12px; text-align: center; color: var(--text-muted);">No results</div>';
                        sidebarSearchResults.style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('Search error:', error);
                });
        }, 300);
    });

    sidebarSearch.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && this.value.trim()) {
            window.location.href = `/wiki/${encodeURIComponent(this.value.trim())}`;
        }
    });

    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!sidebarSearch.contains(e.target) && !sidebarSearchResults.contains(e.target)) {
            sidebarSearchResults.style.display = 'none';
        }
    });
}

// Random Article Navigation
const randomNav = document.getElementById('randomNav');
if (randomNav) {
    randomNav.addEventListener('click', function(e) {
        e.preventDefault();
        fetch('/random')
            .then(response => response.json())
            .then(data => {
                if (data.title) {
                    window.location.href = `/wiki/${encodeURIComponent(data.title)}`;
                }
            })
            .catch(error => {
                console.error('Random article error:', error);
            });
    });
}

// Helper function
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Smooth scroll to top
window.addEventListener('scroll', function() {
    // Future: Add scroll-to-top button if needed
});


