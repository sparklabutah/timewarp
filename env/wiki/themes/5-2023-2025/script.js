// Wikipedia 2025 Theme JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Menu toggle functionality
    const menuToggle = document.getElementById('menuToggle');
    const sideMenu = document.getElementById('sideMenu');
    const menuOverlay = document.getElementById('menuOverlay');
    const menuClose = document.getElementById('menuClose');

    // Open menu
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            sideMenu.classList.add('open');
            menuOverlay.classList.add('active');
            document.body.classList.add('menu-open');
        });
    }

    // Close menu when clicking overlay
    if (menuOverlay) {
        menuOverlay.addEventListener('click', function() {
            sideMenu.classList.remove('open');
            menuOverlay.classList.remove('active');
            document.body.classList.remove('menu-open');
        });
    }

    // Close menu when clicking close button
    if (menuClose) {
        menuClose.addEventListener('click', function() {
            sideMenu.classList.remove('open');
            menuOverlay.classList.remove('active');
            document.body.classList.remove('menu-open');
        });
    }

    // Build table of contents from article headings (like 2004 template)
    (function() {
        const article = document.getElementById('article-content');
        if (!article) return;
        const headings = Array.from(article.querySelectorAll('h2, h3, h4'));
        if (headings.length === 0) return;
        
        const sidebarToc = document.getElementById('leftSidebarToc');
        if (!sidebarToc) return;
        sidebarToc.style.display = 'block';
        
        const list = document.getElementById('tocList');
        if (!list) return;
        
        // Add (Top) link
        const topLi = document.createElement('li');
        topLi.className = 'toc-level-0';
        const topLink = document.createElement('a');
        topLink.href = '#top';
        topLink.textContent = '(Top)';
        topLi.appendChild(topLink);
        list.appendChild(topLi);
        
        let index = 0;
        function slugify(text) {
            return text.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim().replace(/\s+/g, '_').substring(0, 64);
        }
        
        headings.forEach(h => {
            const level = parseInt(h.tagName.substring(1), 10); // 2,3,4
            const text = h.textContent.trim();
            let id = h.id || slugify(text) || ('sec-' + (++index));
            if (!h.id) h.id = id;
            
            const li = document.createElement('li');
            li.className = 'toc-level-' + (level - 1);
            const a = document.createElement('a');
            a.href = '#' + id;
            const textSpan = document.createElement('span');
            textSpan.className = 'toc-text';
            textSpan.textContent = text;
            a.appendChild(textSpan);
            li.appendChild(a);
            list.appendChild(li);
        });
        
        // Toggle functionality
        const toggle = document.getElementById('tocToggle');
        if (toggle) {
            let hidden = false;
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                hidden = !hidden;
                list.style.display = hidden ? 'none' : 'block';
                toggle.textContent = hidden ? '[show]' : '[hide]';
            });
        }
    })();

    // Appearance panel hide functionality
    const appearanceHide = document.querySelector('.appearance-hide');
    const appearancePanel = document.querySelector('.appearance-panel');
    
    if (appearanceHide && appearancePanel) {
        appearanceHide.addEventListener('click', function(e) {
            e.preventDefault();
            appearancePanel.style.display = 'none';
        });
    }
});
