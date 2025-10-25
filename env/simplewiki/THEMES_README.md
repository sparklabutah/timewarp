# WikiReader Themes

WikiReader now supports **multiple UI themes**! Switch between different designs to match your preference.

## 🎨 Available Themes

### 1. Classic Theme (`-1`)

**Traditional Wikipedia-style interface**

- Clean, familiar Wikipedia design
- Top navigation bar
- Traditional layout with sidebar
- Simple and focused
- Light colors and minimal styling

**Features:**

- Search bar in header
- Random article button
- Article sidebar navigation
- Table of contents
- Classic Wikipedia colors

### 2. Modern Theme (`-2`)

**Contemporary dark/light mode interface**

- Sleek sidebar navigation
- Dark mode by default with light mode toggle 🌙 ☀️
- Card-based design
- Gradient accents and modern shadows
- Floating animations
- Emoji icons throughout

**Features:**

- Persistent sidebar with search
- Dark/Light mode switcher
- Modern card layouts
- Gradient hero section
- Colorful topic cards
- Smooth animations
- Mobile-responsive with hamburger menu

### 3. Wikipedia 2002 Theme (`-3`)

**Authentic retro 2002 Wikipedia interface**

- Classic early-2000s web design
- Times New Roman font throughout
- Table-based layout (just like 2002!)
- Simple borders and buttons
- Retro color scheme (blue links, purple visited)
- Left sidebar with classic logo style
- Gray navigation boxes

**Features:**

- Authentic Web 1.0 aesthetic
- Top navigation bar with dropdown
- Language/search bar
- Classic sidebar navigation
- Simple search boxes throughout
- Nostalgic button styles (outset borders!)
- Footer with page info
- Perfect for that early internet nostalgia

### 4. Wikipedia 2001 Theme (`-4`)

**Ultra-minimalist original Wikipedia interface**

- The very first Wikipedia design from 2001
- Absolutely minimal styling
- No sidebar - single column layout
- Pure text-based navigation
- Times New Roman serif font
- Classic blue hyperlinks
- Horizontal rule separators
- No graphics or fancy elements

**Features:**

- Ultra-authentic early internet aesthetic
- "You can edit this page right now!" message
- Simple pipe-separated navigation
- Category lists as plain text links
- Footer date stamp
- Talk section placeholder
- The rawest Wikipedia experience
- Perfect for extreme nostalgia and minimalism

## 🚀 How to Use

### Linux/Mac

```bash
# Classic theme (default)
./start_wiki.sh -1

# Modern theme
./start_wiki.sh -2

# Wikipedia 2002 retro theme
./start_wiki.sh -3

# Wikipedia 2001 ultra-retro theme
./start_wiki.sh -4

# Or run without arguments for classic (default)
./start_wiki.sh
```

### Windows

```cmd
REM Classic theme (default)
start_wiki.bat -1

REM Modern theme
start_wiki.bat -2

REM Wikipedia 2002 retro theme
start_wiki.bat -3

REM Wikipedia 2001 ultra-retro theme
start_wiki.bat -4

REM Or run without arguments for classic (default)
start_wiki.bat
```

### Direct Python

```bash
# Classic theme
python3 wiki_app.py -1
# or
python3 wiki_app.py classic

# Modern theme
python3 wiki_app.py -2
# or
python3 wiki_app.py modern

# Wikipedia 2002 retro theme
python3 wiki_app.py -3
# or
python3 wiki_app.py wikipedia2002

# Wikipedia 2001 ultra-retro theme
python3 wiki_app.py -4
# or
python3 wiki_app.py wikipedia2001
```

## 📁 Folder Structure

```
simplewiki/
├── wiki_app.py              # Main application
├── start_wiki.sh            # Linux/Mac launcher
├── start_wiki.bat           # Windows launcher
│
├── themes/
│   ├── classic/             # Theme 1: Classic Wikipedia-style
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   ├── index.html
│   │   │   ├── article.html
│   │   │   └── 404.html
│   │   └── static/
│   │       ├── style.css
│   │       └── script.js
│   │
│   ├── modern/              # Theme 2: Modern dark/light mode
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   ├── index.html
│   │   │   ├── article.html
│   │   │   └── 404.html
│   │   └── static/
│   │       ├── style.css
│   │       └── script.js
│   │
│   ├── wikipedia2002/       # Theme 3: Wikipedia 2002 retro
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   ├── index.html
│   │   │   ├── article.html
│   │   │   └── 404.html
│   │   └── static/
│   │       ├── style.css
│   │       └── script.js
│   │
│   └── wikipedia2001/       # Theme 4: Wikipedia 2001 ultra-retro
│       ├── templates/
│       │   ├── base.html
│       │   ├── index.html
│       │   ├── article.html
│       │   └── 404.html
│       └── static/
│           ├── style.css
│           └── script.js
│
├── simplewiki-latest-pages-articles.xml  # Wikipedia data
└── wiki_index.pkl          # Cached articles (auto-generated)
```

## 🎯 Theme Comparison

| Feature        | Classic          | Modern            | Wikipedia 2002        | Wikipedia 2001     |
| -------------- | ---------------- | ----------------- | --------------------- | ------------------ |
| **Navigation** | Top bar          | Sidebar           | Top bar + Sidebar     | Top bar only       |
| **Color Mode** | Light only       | Dark/Light toggle | Light only (retro)    | Light only (retro) |
| **Design**     | Traditional      | Card-based        | Table-based (2002)    | Plain text (2001)  |
| **Layout**     | Wikipedia-style  | Modern web app    | Early-2000s web       | Ultra-minimal 2001 |
| **Mobile**     | Basic responsive | Full mobile menu  | Minimal responsive    | Basic              |
| **Animations** | Minimal          | Smooth & modern   | None (authentic!)     | None               |
| **Icons**      | Text-based       | Emoji-based       | Text-based            | None               |
| **Search**     | Header only      | Header + Sidebar  | Multiple search boxes | Footer only        |
| **Font**       | Sans-serif       | System fonts      | Times New Roman       | Times New Roman    |
| **Sidebar**    | Yes              | Yes (sticky)      | Yes (left)            | None               |
| **Graphics**   | Minimal          | Gradients/shadows | Simple borders        | None at all        |
| **Vibe**       | Modern Wikipedia | Sleek 2024        | Nostalgic 2002        | Raw internet 2001  |

## 🛠️ Customization

Each theme has its own isolated files:

- **Templates**: `themes/[theme]/templates/`
- **Styles**: `themes/[theme]/static/style.css`
- **Scripts**: `themes/[theme]/static/script.js`

You can modify any theme without affecting the others!

## 💡 Tips

1. **Modern theme** saves your dark/light preference in browser localStorage
2. All themes use the **same cached data** (wiki_index.pkl)
3. Switch themes **instantly** by restarting with a different argument
4. **No re-indexing needed** when switching themes
5. For the full time-travel experience, try them in order: 2001 → 2002 → Classic → Modern

## 🔧 Creating Your Own Theme

Want to create a custom theme? Follow these steps:

1. Create a new folder: `themes/yourtheme/`
2. Add subfolders: `templates/` and `static/`
3. Copy files from `classic` or `modern` as a starting point
4. Customize the HTML, CSS, and JS
5. Run with: `python3 wiki_app.py yourtheme`

## 🐛 Troubleshooting

**Theme not loading?**

- Make sure you're in the correct directory
- Check that the theme folder exists: `themes/[theme]/`
- Verify templates and static folders contain all required files

**Modern theme not switching colors?**

- Clear browser cache and localStorage
- Check browser console for errors
- Try clicking the moon/sun icon in the sidebar

**Missing styles?**

- Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)
- Check that static files are being served correctly

## 📝 Future Themes

Coming soon:

- **Minimal Theme**: Ultra-clean, distraction-free reading
- **Academic Theme**: Citation-focused with paper-like layout
- **Terminal Theme**: Monospace, hacker-style interface
- **Newspaper Theme**: Print-inspired multi-column layout

---

Enjoy exploring Wikipedia with style! 🎨📚
