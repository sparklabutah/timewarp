# Wikipedia 2002 Retro Theme 🕰️

## Welcome to the Past!

Experience Wikipedia as it looked in **2002** with this authentic retro theme. Travel back to the early days of the internet with table-based layouts, Times New Roman, and classic Web 1.0 design!

## ✨ Features

### Authentic 2002 Design

- **Times New Roman** font throughout (just like 2002!)
- **Table-based layout** (before CSS flexbox existed!)
- **Classic color scheme**: Blue links (#0000EE) and purple visited links (#551A8B)
- **Outset button borders** (that 3D look!)
- **Gray navigation boxes** with simple borders
- **No fancy CSS** - pure early-2000s web design

### Nostalgic Elements

- Top navigation bar with dropdown menu
- Language/search bar with retro styling
- Left sidebar with Wikipedia logo
- Multiple search boxes throughout
- Classic footer with page access info
- Simple horizontal rules (`<hr>`)
- Minimal responsive design (just like 2002!)

### Layout Structure

```
┌─────────────────────────────────────────┐
│  Top Bar (Main Page | Recent Changes)  │
├─────────────────────────────────────────┤
│  Language Bar | Search                  │
├──────────┬──────────────────────────────┤
│          │                              │
│ Sidebar  │  Main Content Area          │
│          │                              │
│ - Logo   │  Article Title              │
│ - Nav    │  Article Content            │
│ - Links  │  Category Links             │
│ - Search │  Footer                     │
│          │                              │
└──────────┴──────────────────────────────┘
```

## 🚀 How to Use

### Linux/Mac

```bash
./start_wiki.sh -3
```

### Windows

```cmd
start_wiki.bat -3
```

### Direct Python

```bash
python3 wiki_app.py -3
# or
python3 wiki_app.py wikipedia2002
```

## 🎨 Design Philosophy

This theme faithfully recreates the look and feel of Wikipedia circa 2002:

### Typography

- **Font**: Times New Roman (the default web font of 2002)
- **Size**: 12pt body, 10pt navigation
- **Links**: Classic underlined blue with purple for visited

### Colors

- **Background**: Pure white (#ffffff)
- **Borders**: Black and gray (#000000, #999999, #aaaaaa)
- **Highlights**: Light gray (#f0f0f0, #e8e8e8)
- **Links**:
  - Normal: #0000EE (classic blue)
  - Visited: #551A8B (classic purple)
  - Active: #FF0000 (red)

### Layout

- **Tables**: Used for main layout (authentic 2002 technique!)
- **No floats or flexbox**: Didn't exist widely in 2002
- **Fixed sidebar**: 180px width
- **Simple borders**: 1px solid lines everywhere

### Buttons

- **Style**: Outset borders (that 3D look!)
- **Background**: #dddddd (light gray)
- **Hover**: Inset on click
- **Font**: Times New Roman, 10pt

## 📝 Technical Details

### File Structure

```
themes/wikipedia2002/
├── templates/
│   ├── base.html       # Main layout with table structure
│   ├── index.html      # Homepage with category links
│   ├── article.html    # Article display
│   └── 404.html        # Error page
└── static/
    ├── style.css       # Retro styling
    └── script.js       # Minimal JavaScript
```

### Key Differences from Modern Themes

| Aspect     | Wikipedia 2002  | Modern Themes    |
| ---------- | --------------- | ---------------- |
| Layout     | `<table>`       | Flexbox/Grid     |
| Font       | Times New Roman | System fonts     |
| Colors     | Fixed palette   | CSS variables    |
| Buttons    | Outset borders  | Flat/shadow      |
| Mobile     | Minimal         | Fully responsive |
| JavaScript | Basic           | Modern ES6+      |
| Animations | None            | CSS transitions  |

## 💡 Why This Theme?

### Nostalgia

Remember when:

- Websites used tables for layout?
- Every site used Times New Roman?
- Buttons had those cool 3D borders?
- Links were always blue and underlined?

### Educational

- See how web design has evolved
- Understand table-based layouts
- Appreciate modern CSS features
- Learn web design history

### Fun

- It's genuinely enjoyable to use!
- Makes reading feel like 2002
- Perfect for a retro project
- Great conversation starter

## 🎯 Perfect For

- **Nostalgic browsing**: Feel like it's 2002 again
- **Retro projects**: Building something with a vintage aesthetic
- **Education**: Teaching web design history
- **Fun**: Just enjoying the classic internet vibes

## 🔧 Customization

The theme is located in:

```
themes/wikipedia2002/
```

You can customize:

- **Colors**: Edit `static/style.css` color values
- **Fonts**: Change font-family (but Times is authentic!)
- **Layout**: Modify table structure in templates
- **Sidebar**: Edit navigation sections

## 🐛 Known Limitations

These are **intentional** to maintain authenticity:

- Minimal mobile responsiveness (phones weren't a thing in 2002!)
- No dark mode (CSS variables weren't invented yet!)
- Table-based layout (that's how we did it!)
- Times New Roman everywhere (it was THE font!)
- Basic JavaScript (jQuery didn't exist yet!)

## 📚 Historical Context

**Wikipedia in 2002:**

- Founded January 2001
- ~90,000 articles by late 2002
- Used table-based layouts
- Classic blue link aesthetic
- Simple, functional design
- No fancy CSS features
- Focused on content over design

This theme captures that era perfectly!

## 🎉 Easter Eggs

Look for these authentic touches:

- "Protected page" links (just like 2002!)
- "Recent changes" alerts (dummy for offline use)
- "This page has been accessed X times" footer
- Language links (non-functional but authentic!)
- Classic dropdown menus
- Outset/inset button effects

## 💭 Feedback

Love the retro vibe? Want to suggest improvements? This theme is part of the WikiReader multi-theme system. Check out:

- `THEMES_README.md` - All themes documentation
- `QUICK_START.md` - Quick setup guide

---

**Time travel complete! Enjoy your 2002 Wikipedia experience!** 🕰️📚

_"This page was last modified 08:12 Nov 13, 2002."_ - Authentic footer vibes!

