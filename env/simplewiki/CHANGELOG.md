# WikiReader Changelog

## Latest Update - Wikipedia 2001 Theme Added! 🎉

### New Feature: Wikipedia 2001 Ultra-Retro Theme

Added a brand new theme that recreates the original Wikipedia interface from **August 2001**!

### What's New

#### Theme 4: Wikipedia 2001 (`-4`)

- **Ultra-minimalist design** - The rawest Wikipedia experience
- **No sidebar** - Single column, text-only layout
- **Pure HTML** - Classic blue links, Times New Roman font
- **Authentic details:**
  - "You can edit this page right now!" message
  - Pipe-separated navigation links
  - Category lists as plain text
  - Footer date stamp
  - Talk section placeholders
  - Simple horizontal rule separators

### Files Added

```
themes/wikipedia2001/
├── templates/
│   ├── base.html       # Ultra-simple base layout
│   ├── index.html      # Homepage with category lists
│   ├── article.html    # Minimal article display
│   └── 404.html        # Simple error page
└── static/
    ├── style.css       # Minimal styling (Times New Roman, blue links)
    └── script.js       # Basically nothing (authentic!)

Documentation:
├── WIKIPEDIA2001_README.md  # Detailed theme documentation
├── THEMES_README.md         # Updated with 2001 theme
└── CHANGELOG.md             # This file
```

### Usage

Launch the 2001 theme with:

**Linux/Mac:**

```bash
./start_wiki.sh -4
```

**Windows:**

```cmd
start_wiki.bat -4
```

**Direct:**

```bash
python3 wiki_app.py -4
# or
python3 wiki_app.py wikipedia2001
```

### Theme Evolution

Now you can experience Wikipedia's complete evolution:

1. **2001 (`-4`)** - The beginning: Ultra-minimal, text-only
2. **2002 (`-3`)** - Early structure: Tables and borders
3. **Classic (`-1`)** - Modern Wikipedia: Clean and familiar
4. **Modern (`-2`)** - Future forward: Dark mode and cards

### Technical Details

- Added `-4` argument support to `wiki_app.py`
- Updated `start_wiki.sh` and `start_wiki.bat`
- Created complete theme folder structure
- Updated documentation files
- All themes share the same cached index (wiki_index.pkl)
- No re-indexing required when switching themes

### Design Philosophy

The 2001 theme is intentionally **extreme minimalism**:

- ❌ No sidebar
- ❌ No graphics
- ❌ No borders or boxes
- ❌ No fancy buttons
- ✅ Just blue links and text
- ✅ Times New Roman font
- ✅ Horizontal rules
- ✅ Pure HTML authenticity

### Historical Accuracy

Based on actual Wikipedia homepage snapshot from **August 8, 2001**:

- Over 8,000 articles (historically accurate count)
- GNU Free Documentation License notice
- Community editing message
- Category scheme listings
- International Wikipedia links
- Project information sections

---

## Previous Updates

### Version 3: Wikipedia 2002 Theme

- Added authentic 2002 retro theme
- Table-based layout with sidebar
- Classic early-2000s web aesthetic

### Version 2: Modern Theme

- Added modern dark/light mode theme
- Card-based design
- Mobile responsive with sidebar

### Version 1: Classic Theme

- Initial Wikipedia-style interface
- Search functionality
- Article rendering with wikitext parsing

### Core Features

- Pre-parsed HTML caching for instant article loading
- Regex-based wikitext to HTML conversion
- Search with live results
- Random article support
- Multiple theme support

---

**Enjoy your journey through Wikipedia history!** 🕰️📚

_From the raw internet of 2001 to the modern web of 2024_


