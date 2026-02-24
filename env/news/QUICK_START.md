# Wikinews Reader - Quick Start Guide

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install Flask mwparserfromhell
```

### 2. Run the Application

```bash
# Windows
start_news.bat

# Linux/Mac
./start_news.sh

# Or directly
python news_app.py
```

### 3. Open in Browser

```
http://localhost:5001
```

## ⏱️ First Run

**Important:** The first time you run the app, it will index the Wikinews dump:

- This takes **10-30 minutes** depending on your system
- A `news_index.pkl` file will be created (~100-200 MB)
- Subsequent runs will be **instant** using the cached index

You'll see progress output like:

```
Parsing Wikinews XML dump and converting to HTML...
Parsed 100 articles (15.3 articles/sec)
Parsed 200 articles (16.1 articles/sec)
...
```

## 🎯 Testing Mode (Faster)

To test quickly with fewer articles, edit `news_app.py` line 23:

```python
MAX_ARTICLES = 1000  # Only index 1000 articles (takes ~2-3 minutes)
```

Then delete `news_index.pkl` and restart the app.

## 📋 Features

- **Search**: Type in the search bar to find articles
- **Browse**: Click "Browse" to see all articles chronologically
- **Random**: Click "Random article" to discover content
- **Categories**: Articles are tagged by topic
- **Responsive**: Works on desktop, tablet, and mobile

## 🔧 Troubleshooting

### Port already in use?

Change port in `news_app.py` (last line):

```python
app.run(debug=True, port=5001)  # Change to 5002, 5003, etc.
```

### Re-index from scratch?

Delete `news_index.pkl` and restart the app.

### Memory issues?

Set `MAX_ARTICLES = 1000` or lower in `news_app.py`.

## 📁 Project Structure

```
env/news/
├── news_app.py                      # Main Flask application
├── enwikinews-latest-pages-*.bz2   # Wikinews XML dump (50 MB)
├── news_index.pkl                   # Cached index (generated)
├── requirements.txt                 # Dependencies
├── start_news.sh / .bat            # Startup scripts
├── templates/                       # HTML templates
│   ├── index.html                  # Homepage
│   ├── article.html                # Article view
│   ├── browse.html                 # Browse all
│   └── 404.html                    # Error page
└── static/                          # CSS & JavaScript
    ├── style.css                   # Modern news UI styles
    └── script.js                   # Search & navigation
```

## 💡 Tips

1. **First Run**: Let it complete the full indexing once
2. **Development**: Use testing mode (`MAX_ARTICLES = 1000`) for faster iterations
3. **Production**: Use full indexing (`MAX_ARTICLES = None`) for all articles
4. **Caching**: Keep `news_index.pkl` - it makes the app instant!

## 🎨 UI Features

- Clean, modern news website design
- Red accent color (#c40000) matching Wikinews branding
- Responsive grid layout for article cards
- Category tags for quick topic identification
- Date-first display for news context
- Smooth animations and transitions

Enjoy browsing Wikinews! 📰
