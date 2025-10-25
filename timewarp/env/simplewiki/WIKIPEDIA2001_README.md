# Wikipedia 2001 Ultra-Retro Theme

## Overview

Experience Wikipedia as it appeared in its very first year - **2001**! This ultra-minimalist theme captures the raw, early internet aesthetic when Wikipedia was just getting started.

![Wikipedia 2001 Theme](screenshot_2001.png)

## Historical Context

In 2001, Wikipedia was brand new:

- **Launched:** January 15, 2001
- **Articles:** Started from scratch, reached 8,000+ by August 2001
- **Technology:** Basic PHP/MySQL, extremely simple HTML
- **Design Philosophy:** Function over form, community-driven content
- **Key Feature:** "You can edit this page right now!" - revolutionary for its time

## Theme Features

### Design Elements

1. **Ultra-Simple Layout**

   - No sidebar navigation
   - Minimal header with just page title and [Home] link
   - Plain text navigation links separated by pipes
   - No fancy graphics or icons
   - Pure HTML/CSS, no JavaScript features

2. **Typography**

   - Times New Roman font (classic serif)
   - 12pt base font size
   - Simple blue hyperlinks (#0000EE)
   - Purple visited links (#551A8B)
   - No custom fonts or webfonts

3. **Visual Style**

   - White background
   - Black text
   - Horizontal rules for section separation
   - No borders, shadows, or gradients
   - Classic early-2000s button styling

4. **Content Organization**

   - Simple category lists with inline links
   - Plain paragraph formatting
   - Basic heading hierarchy
   - Minimal whitespace
   - "Talk" section placeholder at bottom of articles

5. **Navigation**
   - Top navigation: HomePage | RecentChanges | Preferences
   - Footer repeats top navigation
   - Edit links at bottom of each page
   - Date stamp: "Today is Wednesday, August 8, 2001"

### Authentic Details

- **Edit Message:** "You can edit this page right now! It's a free, community project"
- **Welcome Text:** References "over 8,000 articles" and goal of 100,000
- **GNU FDL Notice:** "The content of Wikipedia is covered by the GNU Free Documentation License"
- **Category Schemes:** Listed as simple link lists
- **International Wikipedias:** Basic list with language names
- **Project Info Sections:** Announcements, FAQ, Policy, etc.

## Usage

### Launch the 2001 Theme

**Linux/Mac:**

```bash
./start_wiki.sh -4
```

**Windows:**

```cmd
start_wiki.bat -4
```

### Or specify theme name:

```bash
python3 wiki_app.py wikipedia2001
```

## Technical Details

### File Structure

```
themes/wikipedia2001/
├── templates/
│   ├── base.html      # Base template with 2001 layout
│   ├── index.html     # Homepage with category lists
│   ├── article.html   # Article display page
│   └── 404.html       # Error page
└── static/
    ├── style.css      # Ultra-minimalist styling
    └── script.js      # Minimal JavaScript (almost none!)
```

### CSS Specifications

- **Background:** Pure white (#FFFFFF)
- **Text:** Pure black (#000000)
- **Links:** Standard blue (#0000EE), visited purple (#551A8B)
- **Font:** Times New Roman, 12pt
- **Separators:** 1px solid #AAAAAA
- **Form Elements:** Simple outset border buttons
- **No:** Gradients, shadows, transitions, animations, or modern CSS3 features

### Key Differences from 2002 Theme

| Feature    | 2001 Theme                | 2002 Theme               |
| ---------- | ------------------------- | ------------------------ |
| Layout     | Single column, no sidebar | Table-based with sidebar |
| Navigation | Top bar only              | Sidebar + top bar        |
| Logo       | None (just text)          | Simple "W" icon          |
| Styling    | Plain text                | Boxes and borders        |
| Search     | Bottom of page            | Sidebar + footer         |
| Sections   | Inline text               | Structured boxes         |
| Complexity | Minimal                   | Moderate                 |

## The Wikipedia Time Machine

This theme is part of a series that lets you experience Wikipedia's evolution:

1. **Wikipedia 2001** (-4): The very beginning - ultra-minimal
2. **Wikipedia 2002** (-3): Early structure - boxes and tables
3. **Modern Dark/Light** (-2): Contemporary card-based design
4. **Classic** (-1): Current Wikipedia style

## Historical Notes

### August 8, 2001

The default date shown ("Wednesday, August 8, 2001") is from the actual Wikipedia homepage snapshot we based this theme on. At this point:

- Wikipedia had grown to over 8,000 articles in English
- The community was establishing policies and guidelines
- Jimmy Wales and Larry Sanger were actively involved in development
- The site was still running on UseModWiki software (before MediaWiki)

### Early Wikipedia Philosophy

The prominent "You can edit this page right now!" message reflects Wikipedia's revolutionary concept at the time:

- Anyone could contribute without registration
- No central editorial control
- Community-driven quality through peer review
- Free content under GNU FDL

### Technical Limitations

The ultra-simple design wasn't just aesthetic - it reflected the technical constraints of 2001:

- Limited bandwidth (many users still on dial-up)
- Basic web browsers (IE 5, Netscape 4)
- Server capacity concerns
- Simple PHP/MySQL stack

## Nostalgia Factor

This theme will feel familiar if you:

- Used the internet in the early 2000s
- Remember GeoCities and basic HTML sites
- Appreciate the "old web" aesthetic
- Value function over form
- Miss when websites were just plain text and blue links

## Perfect For

- **Historians:** Study Wikipedia's early design
- **Researchers:** Focus on content without distractions
- **Nostalgia Seekers:** Relive the early internet
- **Minimalists:** Enjoy ultra-simple interfaces
- **Educators:** Show students web design evolution

## Fun Facts

- The original Wikipedia homepage had NO logo!
- "Wikipedia" wasn't trademarked yet
- Articles had no inline citations (those came later)
- The "Neutral Point of View" policy was still being developed
- The first Wikipedia meetup hadn't happened yet

---

**Experience the internet as it was meant to be: Simple, accessible, and collaborative!**

_"You can edit this page right now! It's a free, community project"_

