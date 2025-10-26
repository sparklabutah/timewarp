# Wikinews Reader

A modern web interface for browsing Wikinews articles from a local XML dump.

## Features

- 🎨 **Modern News UI** - Clean, responsive design optimized for news reading
- 📰 **Full Wikinews Archive** - Browse all articles from the Wikinews dump
- 🔍 **Fast Search** - Real-time search through article titles
- 🏷️ **Category Tags** - Articles organized by categories
- 📅 **Chronological Browsing** - Articles sorted by publication date
- ⚡ **Pre-parsed Content** - HTML is cached for instant page loads
- 🎲 **Random Article** - Discover news articles randomly

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Wikinews Dump

The application uses the English Wikinews dump:

- File: `enwikinews-latest-pages-articles-multistream.xml.bz2`
- URL: https://dumps.wikimedia.org/enwikinews/latest/
- This file should already be in the `env/news/` directory

### 3. First Run (Indexing)

The first time you run the application, it will parse the XML dump and create an index. This takes time but only happens once:

```bash
# Linux/Mac
./start_news.sh

# Windows
start_news.bat

# Or directly
python news_app.py
```

**Indexing time:** Approximately 10-30 minutes depending on your system.

The application will create a `news_index.pkl` file that caches all parsed articles for instant serving.

### 4. Access the Application

Once indexing is complete, open your browser and go to:

```
http://localhost:5001
```

## Usage

### Browse News

- **Homepage**: Shows the 20 most recent news articles
- **Browse Page**: Navigate through all articles with pagination
- **Search**: Use the search bar to find articles by title
- **Random Article**: Click "Random article" to discover content

### Article View

- Full article content with formatting
- Publication date prominently displayed
- Category tags for navigation
- Table of contents for longer articles
- Related navigation links

## Configuration

### Testing Mode

For faster testing, edit `news_app.py` and set:

```python
MAX_ARTICLES = 1000  # Limit to first 1000 articles
```

Set to `None` for full indexing:

```python
MAX_ARTICLES = None  # Process all articles
```

### Change Port

Default port is `5001`. To change it, edit the last line in `news_app.py`:

```python
app.run(debug=True, port=5001)  # Change port number here
```

## File Structure

```
env/news/
├── news_app.py                    # Flask backend application
├── requirements.txt               # Python dependencies
├── start_news.sh                  # Linux/Mac startup script
├── start_news.bat                 # Windows startup script
├── enwikinews-latest-pages-*.bz2 # Wikinews XML dump (compressed)
├── news_index.pkl                 # Cached article index (generated)
├── templates/                     # HTML templates
│   ├── base.html                  # Base template
│   ├── index.html                 # Homepage
│   ├── article.html               # Article view
│   ├── browse.html                # Browse all articles
│   └── 404.html                   # Error page
└── static/                        # CSS and JavaScript
    ├── style.css                  # News UI styles
    └── script.js                  # Client-side functionality
```

## Technical Details

### Article Parsing

- Uses `xml.etree.ElementTree` for efficient XML parsing
- Wikitext is converted to HTML using regex-based parsing
- Categories are extracted from article metadata
- Articles are sorted by publication date

### Performance Optimization

- All articles are pre-parsed during indexing
- HTML content is cached in memory and on disk
- Search uses case-insensitive title matching
- Pagination limits results per page for fast loading

### Memory Usage

- Full index is loaded into memory for fast access
- Typical memory usage: 200-500 MB for full Wikinews archive
- Disk cache size: ~100-200 MB

## Troubleshooting

### Issue: "File not found" error

**Solution**: Make sure the Wikinews XML dump is in the `env/news/` directory.

### Issue: Indexing is too slow

**Solution**:

1. Set `MAX_ARTICLES = 1000` for testing
2. Use an SSD for faster file I/O
3. Increase Python memory if parsing fails

### Issue: Port already in use

**Solution**: Change the port in `news_app.py` or stop the other application using port 5001.

### Issue: Search not working

**Solution**: Make sure JavaScript is enabled in your browser.

## License

This application is a reader interface for Wikinews content. All Wikinews content is licensed under the Creative Commons Attribution 2.5 License.

- **Wikinews**: https://en.wikinews.org/
- **Wikimedia Dumps**: https://dumps.wikimedia.org/
- **License**: https://creativecommons.org/licenses/by/2.5/

## Credits

- Built with Flask (Python web framework)
- Wikinews content from Wikimedia Foundation
- Modern UI design inspired by contemporary news websites
