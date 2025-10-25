# Simple Wikipedia UI

A beautiful, Wikipedia-style user interface for browsing Simple Wikipedia XML dumps locally.

## Features

✨ **Full Wikipedia Experience**

- Clean, modern UI matching Wikipedia's design
- Article rendering with proper formatting
- Search functionality with live suggestions
- Random article discovery
- Table of contents generation
- Mobile-responsive design

🚀 **Fast & Efficient**

- Caches article index for quick searches
- Streams large XML files efficiently
- Client-side search with instant results

## Installation

1. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

2. **Make sure your Wikipedia XML dump is in the root directory:**
   - The file should be named: `simplewiki-latest-pages-articles.xml`
   - Or update the `XML_DUMP_PATH` variable in `wiki_app.py`

## Usage

1. **Start the application:**

```bash
python wiki_app.py
```

2. **First Run:**

   - The first time you run the app, it will index all articles from the XML dump
   - This may take 5-10 minutes depending on the dump size
   - The index will be cached in `wiki_index.pkl` for future runs

3. **Open your browser:**
   - Navigate to: `http://localhost:5000`
   - Start searching and reading articles!

## How It Works

### Backend (Flask)

- **XML Parsing**: Efficiently streams through the XML dump using `iterparse`
- **Indexing**: Creates a searchable index of all article titles
- **Search**: Returns matching articles based on title search
- **Article Retrieval**: Fetches full article content on-demand
- **Wikitext Conversion**: Converts MediaWiki markup to HTML

### Frontend

- **Search**: Live search with autocomplete suggestions
- **Article View**: Clean, readable article pages
- **Navigation**: Sidebar navigation and table of contents
- **Random**: Discover random articles
- **Responsive**: Works on desktop, tablet, and mobile

## File Structure

```
TimeWarp/
├── wiki_app.py                      # Flask backend application
├── requirements.txt                 # Python dependencies
├── simplewiki-latest-pages-articles.xml  # Wikipedia XML dump (you provide)
├── wiki_index.pkl                   # Cached article index (auto-generated)
├── templates/
│   ├── base.html                    # Base template
│   ├── index.html                   # Homepage
│   ├── article.html                 # Article page
│   └── 404.html                     # Error page
└── static/
    ├── style.css                    # All CSS styles
    └── script.js                    # Frontend JavaScript
```

## Features Explained

### Search

- Type in the search bar to find articles
- Results appear instantly as you type
- Click any result to view the article
- Press Enter to search for exact title

### Random Article

- Click "Random article" button anywhere
- Instantly loads a random article from the database

### Table of Contents

- Automatically generated from article headings
- Click to jump to any section
- Smooth scrolling

### Wikitext Rendering

- Converts MediaWiki markup to readable HTML
- Supports:
  - Headings (==, ===, etc.)
  - Bold and italic text
  - Internal links to other articles
  - External links
  - Bullet lists
  - And more!

## Customization

### Changing the Port

Edit `wiki_app.py` line near the end:

```python
app.run(debug=True, port=5000)  # Change 5000 to your preferred port
```

### Styling

All styles are in `static/style.css`. Customize colors, fonts, and layouts to your preference.

### XML Dump Path

If your XML dump has a different name or location, update in `wiki_app.py`:

```python
XML_DUMP_PATH = 'path/to/your/dump.xml'
```

## Performance Tips

1. **First run takes time**: Indexing 200k+ articles takes a few minutes
2. **Keep the cache**: Don't delete `wiki_index.pkl` - it makes subsequent runs instant
3. **XML file size**: The app streams the XML, so even 200MB+ files work fine
4. **Memory usage**: ~200-300MB for the index, minimal for serving pages

## Troubleshooting

### "Article not found"

- Make sure the article exists in your dump
- Try searching to see available articles
- Check spelling and capitalization

### Slow first start

- This is normal - indexing takes time
- Wait for "Indexing complete!" message
- Next runs will be instant

### Search not working

- Make sure Flask is running
- Check browser console for errors
- Verify `wiki_index.pkl` was created

### XML parsing errors

- Ensure your XML dump is valid
- Try downloading a fresh copy
- Check file permissions

## Requirements

- Python 3.7+
- Flask 3.0.0
- mwparserfromhell 0.6.6

## License

This is a reader interface for Wikipedia content. Wikipedia content is available under the Creative Commons Attribution-ShareAlike License.

## Acknowledgments

- Built for browsing Simple Wikipedia dumps
- Styled to match Wikipedia's clean, accessible design
- Uses efficient XML streaming for large files

Enjoy exploring Wikipedia offline! 📚
