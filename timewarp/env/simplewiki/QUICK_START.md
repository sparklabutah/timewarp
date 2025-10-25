# WikiReader - Quick Start Guide

## 🚀 Launch the App

### Option 1: Classic Theme (Wikipedia-style)

```bash
./start_wiki.sh -1
```

### Option 2: Modern Theme (Dark/Light mode)

```bash
./start_wiki.sh -2
```

### Windows Users

```cmd
start_wiki.bat -1   (Classic)
start_wiki.bat -2   (Modern)
```

## 📸 Theme Previews

### Classic Theme (`-1`)

- Traditional Wikipedia look and feel
- Top navigation bar
- Light color scheme
- Simple and familiar

### Modern Theme (`-2`)

- Sidebar navigation
- Dark mode by default
- Light/Dark toggle button (🌙/☀️)
- Card-based modern design
- Gradients and animations
- Colorful topic cards

## 🔄 Switching Themes

1. Stop the current server (Ctrl+C)
2. Run with different argument:
   - `-1` for Classic
   - `-2` for Modern
   - `-3` for Wikipedia 2002 (Retro!)
3. Refresh your browser

**Note:** Both themes use the same cached data - no need to re-index!

## 💡 First Time Setup

1. Make sure `simplewiki-latest-pages-articles.xml` is in the folder
2. Run: `./start_wiki.sh -2` (or `-1` for classic)
3. Wait for indexing to complete (~20-30 min for full dataset)
4. Open browser to: `http://localhost:5000`
5. Start exploring!

## 🎯 Tips

- **Modern theme**: Your dark/light preference is saved
- **Search**: Works in both header and sidebar (modern theme)
- **Random**: Click the 🎲 button for random articles
- **Mobile**: Modern theme has full mobile support

## 📚 Documentation

- `THEMES_README.md` - Detailed theme documentation
- `README_WIKI.md` - Full application guide
- `OPTIMIZATIONS.md` - Technical details

---

**Enjoy your Wikipedia reading experience!** 📖✨
