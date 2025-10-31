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

// Build Table of Contents on page load
document.addEventListener('DOMContentLoaded', function() {
    buildTableOfContents();
});

function buildTableOfContents() {
    const articleBody = document.getElementById('article-body');
    const tocContainer = document.getElementById('toc-container');
    
    if (!articleBody || !tocContainer) return;
    
    // Find all headings (h2-h6)
    const headings = articleBody.querySelectorAll('h2, h3, h4, h5, h6');
    
    // Only show TOC if there are 3+ headings
    if (headings.length < 3) return;
    
    // Create TOC structure
    const toc = document.createElement('div');
    toc.className = 'toc';
    
    // TOC header
    const tocTitle = document.createElement('div');
    tocTitle.className = 'toc-title';
    tocTitle.innerHTML = '<strong>Table of contents</strong> <span class="toc-toggle">[<a href="#" id="toc-toggle-link">hide</a>]</span>';
    toc.appendChild(tocTitle);
    
    // TOC list
    const tocList = document.createElement('ul');
    tocList.className = 'toc-list';
    tocList.id = 'toc-list';
    
    // Counters for numbering
    const counters = [0, 0, 0, 0, 0];
    let lastLevel = 2;
    
    headings.forEach((heading, index) => {
        const level = parseInt(heading.tagName.substring(1)); // h2 -> 2, h3 -> 3, etc.
        const adjustedLevel = level - 2; // Make h2 = level 0
        
        // Add ID to heading for linking
        if (!heading.id) {
            heading.id = 'section-' + index;
        }
        
        // Update counters
        if (level > lastLevel) {
            // Going deeper
            counters[adjustedLevel]++;
        } else if (level === lastLevel) {
            // Same level
            counters[adjustedLevel]++;
        } else {
            // Going up, reset deeper levels
            for (let i = adjustedLevel + 1; i < counters.length; i++) {
                counters[i] = 0;
            }
            counters[adjustedLevel]++;
        }
        lastLevel = level;
        
        // Build number string (e.g., "1.2.3")
        let numberStr = '';
        for (let i = 0; i <= adjustedLevel; i++) {
            if (counters[i] > 0) {
                numberStr += counters[i] + '.';
            }
        }
        numberStr = numberStr.slice(0, -1); // Remove trailing dot
        
        // Create TOC item
        const tocItem = document.createElement('li');
        tocItem.className = 'toc-level-' + (adjustedLevel + 1);
        tocItem.innerHTML = '<span class="toc-number">' + numberStr + '</span><a href="#' + heading.id + '">' + heading.textContent + '</a>';
        tocList.appendChild(tocItem);
    });
    
    toc.appendChild(tocList);
    tocContainer.appendChild(toc);
    
    // Toggle functionality
    const toggleLink = document.getElementById('toc-toggle-link');
    if (toggleLink) {
        toggleLink.addEventListener('click', function(e) {
            e.preventDefault();
            const list = document.getElementById('toc-list');
            if (list.style.display === 'none') {
                list.style.display = 'block';
                toggleLink.textContent = 'hide';
            } else {
                list.style.display = 'none';
                toggleLink.textContent = 'show';
            }
        });
    }
}


