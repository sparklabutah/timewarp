"""
Wikinews UI - Flask Backend
Parses Wikinews XML dump and serves news articles with a modern news UI
Uses mwparserfromhell for proper MediaWiki parsing and HTML pre-caching
"""

import xml.etree.ElementTree as ET
import re
from html import escape
from flask import Flask, render_template, request, jsonify, send_from_directory
import pickle
import os
import random
from datetime import datetime
import sys
import mwparserfromhell
import socket
import subprocess
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def _parse_args(argv):
    """Parse CLI args for theme selection and optional port override."""
    num_to_theme = {
        '1': '1-2000s',
        '2': '2-2004s',
        '3': '3-2008s',
        '4': '4-2016s',
        '5': '5-2024s',
        '6': '6-base-minimal',
    }
    name_aliases = {
        'minimal': '6-base-minimal',
        'base': '6-base-minimal',
        'classic': '6-base-minimal',
        '2000': '1-2000s',
        '2000s': '1-2000s',
        '2004': '2-2004s',
        '2004s': '2-2004s',
        '2008': '3-2008s',
        '2008s': '3-2008s',
        '2016': '4-2016s',
        '2016s': '4-2016s',
        '2024': '5-2024s',
        '2024s': '5-2024s',
        'all': 'all',
    }
    selected_theme = '6-base-minimal'
    port_override = None
    run_all = False
    for raw in argv[1:]:
        arg = raw.lstrip('-').lower()
        if raw.startswith('--port='):
            try:
                port_override = int(raw.split('=', 1)[1])
            except Exception:
                pass
            continue
        if arg in num_to_theme:
            selected_theme = num_to_theme[arg]
        elif arg in name_aliases:
            if name_aliases[arg] == 'all':
                run_all = True
            else:
                selected_theme = name_aliases[arg]
    return selected_theme, port_override, run_all


# Determine theme and port from command line arguments
THEME, PORT_OVERRIDE, RUN_ALL = _parse_args(sys.argv)

print(f"Using theme: {THEME}")

# Initialize Flask with theme-specific paths
app = Flask(__name__,
            template_folder=os.path.join(SCRIPT_DIR, 'themes', THEME),
            static_folder=os.path.join(SCRIPT_DIR, 'themes', THEME))

# Custom Jinja2 filters
def article_url_filter(title):
    """
    Generate proper URL for article titles.
    If title starts with http:// or https://, return it as-is (external link).
    Otherwise, return local article path.
    """
    if title and (title.startswith('http://') or title.startswith('https://')):
        return title
    return f"/news/{title}"

def is_external_link_filter(title):
    """Check if a title is an external HTTP/HTTPS link"""
    return title and (title.startswith('http://') or title.startswith('https://'))

# Register filters explicitly
app.jinja_env.filters['article_url'] = article_url_filter
app.jinja_env.filters['is_external_link'] = is_external_link_filter

# Paths relative to the script location
XML_DUMP_PATH = os.path.join(SCRIPT_DIR, 'enwikinews-latest-pages-articles-multistream.xml.bz2')
INDEX_CACHE_PATH = os.path.join(SCRIPT_DIR, 'news_index.pkl')

# Optional: Limit number of articles for testing
MAX_ARTICLES = None  # Set to 1000 for testing

# Global index of news articles
article_index = {}
articles_by_date = []  # List of articles sorted by date


def extract_category(text):
    """Extract category from article text"""
    categories = []
    matches = re.findall(r'\[\[Category:(.*?)\]\]', text, flags=re.IGNORECASE)
    for match in matches:
        cat = match.split('|')[0].strip()
        if cat and cat not in ['Pages', 'Published', 'Articles', 'Archived']:
            categories.append(cat)
    return categories[:3]  # Limit to 3 categories


def parse_and_clean_wikitext(wikitext):
    """
    Parse wikitext and return cleaned HTML for news articles
    Uses mwparserfromhell for proper MediaWiki parsing
    """
    if not wikitext:
        return ""
    
    try:
        # Convert tables FIRST before mwparserfromhell processes them
        # (mwparserfromhell doesn't handle tables well)
        wikitext = convert_wikitables_to_html(wikitext)
        
        # Parse wikitext using mwparserfromhell
        wikicode = mwparserfromhell.parse(wikitext)
        
        # Remove templates
        templates = wikicode.filter_templates()
        for template in templates:
            try:
                wikicode.remove(template)
            except:
                pass
        
        # Remove comments
        comments = wikicode.filter_comments()
        for comment in comments:
            try:
                wikicode.remove(comment)
            except:
                pass
        
        # Remove tags (like <ref>, <gallery>, etc.)
        tags = wikicode.filter_tags()
        for tag in tags:
            try:
                wikicode.remove(tag)
            except:
                pass
        
        # Remove file/image links and category links using wikilinks filter
        wikilinks = wikicode.filter_wikilinks()
        for link in wikilinks:
            try:
                title = str(link.title)
                # Remove if it's a File:, Image:, or Category: link
                if title.lower().startswith(('file:', 'image:', 'category:')):
                    wikicode.remove(link)
            except:
                pass
        
        # Get the cleaned wikitext
        cleaned_wikitext = str(wikicode)
        
        # Remove __NOTOC__, __FORCETOC__, etc.
        cleaned_wikitext = re.sub(r'__[A-Z]+__', '', cleaned_wikitext)
        
        # Clean up extra whitespace
        cleaned_wikitext = re.sub(r'\n\n+', '\n\n', cleaned_wikitext)
        
        # Convert remaining wikitext to HTML
        html = convert_wikitext_to_html(cleaned_wikitext)
        
        return html
        
    except Exception as e:
        print(f"Error parsing wikitext: {e}")
        # Fallback: return basic paragraphs
        return '<p>' + '</p><p>'.join(wikitext.split('\n\n')[:10]) + '</p>'


def convert_wikitext_to_html(text):
    """Convert wikitext markup to HTML"""
    # Convert headings
    text = re.sub(r'^======\s*(.*?)\s*======', r'<h6>\1</h6>', text, flags=re.MULTILINE)
    text = re.sub(r'^=====\s*(.*?)\s*=====', r'<h5>\1</h5>', text, flags=re.MULTILINE)
    text = re.sub(r'^====\s*(.*?)\s*====', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^===\s*(.*?)\s*===', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^==\s*(.*?)\s*==', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    
    # Convert bold and italic
    text = re.sub(r"'''''(.*?)'''''", r'<strong><em>\1</em></strong>', text)
    text = re.sub(r"'''(.*?)'''", r'<strong>\1</strong>', text)
    text = re.sub(r"''(.*?)''", r'<em>\1</em>', text)
    
    # Helper function to clean interwiki prefixes from links
    def clean_link(match):
        link = match.group(1)
        display = match.group(2) if len(match.groups()) > 1 else link
        # Remove interwiki prefixes (w:, en:, etc.)
        cleaned_link = re.sub(r'^[a-z]{1,10}:', '', link)
        cleaned_display = re.sub(r'^[a-z]{1,10}:', '', display)
        return f'<a href="/news/{cleaned_link}">{cleaned_display}</a>'
    
    # Convert internal links [[Link|Display]] and [[Link]]
    text = re.sub(r'\[\[([^\|\]]+)\|([^\]]+)\]\]', clean_link, text)
    text = re.sub(r'\[\[([^\]]+)\]\]', clean_link, text)
    
    # Convert external links
    text = re.sub(r'\[https?:([^\s\]]+)\s+([^\]]+)\]', r'<a href="http\1" target="_blank">\2</a>', text)
    
    # Convert lists
    lines = text.split('\n')
    result = []
    in_ul = False
    in_ol = False
    
    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith('*'):
            if not in_ul:
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                result.append('<ul>')
                in_ul = True
            item = stripped.lstrip('*').strip()
            result.append(f'<li>{item}</li>')
        elif stripped.startswith('#'):
            if not in_ol:
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                result.append('<ol>')
                in_ol = True
            item = stripped.lstrip('#').strip()
            result.append(f'<li>{item}</li>')
        else:
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if in_ol:
                result.append('</ol>')
                in_ol = False
            if stripped:
                result.append(f'<p>{line}</p>')
    
    if in_ul:
        result.append('</ul>')
    if in_ol:
        result.append('</ol>')
    
    return '\n'.join(result)


# --- MediaWiki table conversion (lightweight) ---
TABLE_RE = re.compile(r"\{\|[\s\S]*?\|\}", re.MULTILINE)


def _attrs_to_html(attrs: str) -> str:
    attrs = attrs.strip()
    return f" {attrs}" if attrs else ""


def _split_cells(line: str):
    if line.startswith("!"):
        sep = "!!" if "!!" in line else "!"
        cells = [c.strip() for c in line.split(sep) if c.strip() != ""]
        return [("th", c) for c in cells]
    if line.startswith("|"):
        if "||" in line:
            return [("td", p.strip()) for p in line.split("||")]
        return [("td", line[1:].strip())]
    return []


def _render_cell(tag: str, raw: str) -> str:
    if "|" in raw:
        params, text = raw.split("|", 1)
        return f"<{tag}{_attrs_to_html(params)}>{escape(text.strip())}</{tag}>"
    return f"<{tag}>{escape(raw.strip())}</{tag}>"


def _wikitable_to_html(table_text: str) -> str:
    lines = table_text.strip().splitlines()
    if not lines or not lines[0].startswith("{|"):
        return table_text
    table_attrs = lines[0][2:].strip()
    html_parts = [f"<table{_attrs_to_html(table_attrs)}>"]
    in_row = False
    for line in lines[1:]:
        line = line.rstrip()
        if not line:
            continue
        if line.startswith("|}"):
            if in_row:
                html_parts.append("</tr>")
                in_row = False
            html_parts.append("</table>")
            break
        if line.startswith("|-"):
            if in_row:
                html_parts.append("</tr>")
            row_attrs = line[2:].strip()
            html_parts.append(f"<tr{_attrs_to_html(row_attrs)}>")
            in_row = True
            continue
        if line.startswith(("|", "!")):
            cells = _split_cells(line)
            if cells:
                if not in_row:
                    html_parts.append("<tr>")
                    in_row = True
                for tag, raw in cells:
                    html_parts.append(_render_cell(tag, raw))
            continue
        if in_row:
            html_parts.append(f"<td>{escape(line.strip())}</td>")
    return "\n".join(html_parts)


def convert_wikitables_to_html(wikitext: str) -> str:
    def _repl(m):
        return _wikitable_to_html(m.group(0))
    return TABLE_RE.sub(_repl, wikitext)


def parse_xml_dump():
    """Parse the Wikinews XML dump and create an index"""
    import time
    import bz2
    
    print("="*70)
    print("Parsing Wikinews XML dump and converting to HTML...")
    if MAX_ARTICLES:
        print(f"TESTING MODE: Limiting to {MAX_ARTICLES} articles")
    else:
        print("FULL MODE: Processing ALL articles")
    print("="*70)
    
    # XML namespace
    ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
    
    # Open bz2 compressed file
    with bz2.open(XML_DUMP_PATH, 'rb') as f:
        context = ET.iterparse(f, events=('start', 'end'))
        context = iter(context)
        
        count = 0
        start_time = time.time()
        articles_list = []
        
        for event, elem in context:
            if event == 'end' and elem.tag == '{http://www.mediawiki.org/xml/export-0.11/}page':
                # Extract page data
                title_elem = elem.find('mw:title', ns)
                ns_elem = elem.find('mw:ns', ns)
                text_elem = elem.find('.//mw:text', ns)
                timestamp_elem = elem.find('.//mw:timestamp', ns)
                
                if title_elem is not None and ns_elem is not None and text_elem is not None:
                    title = title_elem.text
                    namespace = ns_elem.text
                    text = text_elem.text or ""
                    timestamp = timestamp_elem.text if timestamp_elem is not None else ""
                    
                    # Only index main namespace articles (ns=0)
                    if namespace == '0' and title and len(text) > 100:
                        # Extract categories
                        categories = extract_category(text)
                        
                        # Parse wikitext to HTML
                        html_content = parse_and_clean_wikitext(text)
                        
                        # Extract date from title (Wikinews format often includes dates)
                        date_match = re.search(r'(\d{4})', title)
                        year = date_match.group(1) if date_match else '2024'
                        
                        # Parse timestamp
                        date_obj = None
                        try:
                            date_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except:
                            date_obj = datetime.now()
                        
                        article_data = {
                            'title': title,
                            'html': html_content,
                            'timestamp': timestamp,
                            'date': date_obj,
                            'categories': categories,
                            'year': year
                        }
                        
                        # Store in index
                        article_index[title.lower()] = article_data
                        articles_list.append(article_data)
                        count += 1
                        
                        # Progress reporting
                        if count % 100 == 0:
                            elapsed = time.time() - start_time
                            rate = count / elapsed if elapsed > 0 else 0
                            print(f"Parsed {count} articles ({rate:.1f} articles/sec)")
                        
                        # Check limit
                        if MAX_ARTICLES and count >= MAX_ARTICLES:
                            print(f"\nReached limit of {MAX_ARTICLES} articles")
                            break
                
                # Clear element to free memory
                elem.clear()
    
    elapsed = time.time() - start_time
    print("="*70)
    print(f"Indexing complete! Total articles: {count}")
    print(f"Total time: {elapsed:.1f} seconds")
    print("="*70)
    
    # Sort articles by date (newest first)
    articles_list.sort(key=lambda x: x['date'], reverse=True)
    
    # Save index to cache
    print("Saving index to cache...")
    cache_data = {
        'index': article_index,
        'by_date': articles_list
    }
    with open(INDEX_CACHE_PATH, 'wb') as f:
        pickle.dump(cache_data, f)
    
    cache_size_mb = os.path.getsize(INDEX_CACHE_PATH) / (1024 * 1024)
    print(f"Cache saved ({cache_size_mb:.1f} MB)")
    
    return article_index, articles_list


def load_or_create_index():
    """Load cached index or create new one"""
    global article_index, articles_by_date
    
    if os.path.exists(INDEX_CACHE_PATH):
        print("Loading cached index...")
        with open(INDEX_CACHE_PATH, 'rb') as f:
            cache_data = pickle.load(f)
        article_index = cache_data['index']
        articles_by_date = cache_data['by_date']
        print(f"Loaded {len(article_index)} articles from cache")
    else:
        article_index, articles_by_date = parse_xml_dump()
    
    return article_index, articles_by_date


@app.route('/assets/<filename>')
def assets(filename):
    """Serve files from the assets folder"""
    return send_from_directory(os.path.join(SCRIPT_DIR, 'assets'), filename)


@app.route('/')
def index():
    """Main news page"""
    # Get recent articles
    recent = articles_by_date[:20]  # Top 20 most recent
    return render_template('index.html', recent_articles=recent)


@app.route('/news/<title>')
def article(title):
    """Display a news article"""
    # Look up article in index (case-insensitive)
    article_data = article_index.get(title.lower())
    
    if not article_data:
        return render_template('404.html', title=title), 404
    
    # Format date
    date_str = article_data['date'].strftime('%B %d, %Y') if article_data.get('date') else 'Unknown date'
    
    return render_template('article.html', 
                         title=article_data['title'],
                         content=article_data['html'],
                         date=date_str,
                         categories=article_data.get('categories', []))


def strip_html(html):
    """Remove HTML tags and return plain text"""
    if not html:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Decode HTML entities (basic ones)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


@app.route('/search')
def search():
    """Search for articles - searches in title, content, and categories"""
    query = request.args.get('q', '').strip()
    page = int(request.args.get('page', 1))
    # Classic theme uses 3x3 grid, so 9 items per page
    per_page = 9 if THEME == 'classic' else 10
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not query:
        if is_ajax:
            return jsonify([])
        return render_template('search.html', 
                             query='', 
                             results=[],
                             page=1,
                             total_pages=0,
                             total_results=0,
                             theme=THEME)
    
    # Split query into individual words
    query_words = re.findall(r'\b\w+\b', query.lower())
    if not query_words:
        if is_ajax:
            return jsonify([])
        return render_template('search.html', 
                             query=query, 
                             results=[],
                             page=1,
                             total_pages=0,
                             total_results=0,
                             theme=THEME)
    
    query_lower = query.lower()
    results = []
    
    # Search in article index
    for key, data in article_index.items():
        title = data.get('title', '')
        title_lower = title.lower()
        # Get categories
        categories = data.get('categories', [])
        categories_text = ' '.join([cat.lower() for cat in categories])
        
        # Calculate relevance score (TITLE AND CATEGORY ONLY - faster search)
        score = 0
        matches = []
        
        # Title matches (highest priority)
        if query_lower in title_lower:
            score += 100  # Exact phrase in title
            matches.append('title')
        else:
            # Count word matches in title
            title_word_matches = sum(1 for word in query_words if word in title_lower)
            if title_word_matches > 0:
                score += title_word_matches * 50  # Each word match in title
                matches.append(f'title ({title_word_matches} words)')
        
        # Category matches (medium priority)
        if query_lower in categories_text:
            score += 30  # Exact phrase in categories
            matches.append('category')
        else:
            category_word_matches = sum(1 for word in query_words if word in categories_text)
            if category_word_matches > 0:
                score += category_word_matches * 20  # Each word match in categories
                matches.append(f'category ({category_word_matches} words)')
        
        # Only include if at least one word matched
        if score > 0:
            date_str = data['date'].strftime('%Y-%m-%d') if data.get('date') else ''
            results.append({
                'title': title,
                'date': date_str,
                'date_obj': data.get('date'),  # Keep original date object for sorting
                'score': score,
                'matches': ', '.join(matches) if matches else 'content'
            })
    
    # Sort by relevance score (highest first), then by date (newest first)
    # Use negative score for descending order, and negative timestamp for newest first
    results.sort(key=lambda x: (
        -x['score'], 
        -(x['date_obj'].timestamp() if x.get('date_obj') else 0)
    ))
    
    # Calculate pagination
    total_results = len(results)
    total_pages = (total_results + per_page - 1) // per_page
    
    # Get results for current page
    start = (page - 1) * per_page
    end = start + per_page
    page_results = results[start:end]
    
    # Debug output
    print(f"Search: '{query}' | Total: {total_results} | Page: {page}/{total_pages} | Showing: {len(page_results)} results")
    
    # Remove score, matches, and date_obj from response (only used for sorting)
    for result in page_results:
        result.pop('score', None)
        result.pop('matches', None)
        result.pop('date_obj', None)
    
    # Return JSON for AJAX requests
    if is_ajax:
        return jsonify(page_results[:500])  # Limit for AJAX
    
    # Return HTML page for direct navigation
    return render_template('search.html', 
                         query=query, 
                         results=page_results,
                         page=page,
                         total_pages=total_pages,
                         total_results=total_results,
                         theme=THEME)


@app.route('/random')
def random_article():
    """Get a random article"""
    if article_index:
        random_key = random.choice(list(article_index.keys()))
        return jsonify({'title': article_index[random_key]['title']})
    return jsonify({'title': None})


@app.route('/browse')
def browse():
    """Browse all articles chronologically"""
    page = int(request.args.get('page', 1))
    # Classic theme uses 3x3 grid, so 9 items per page
    per_page = 9 if THEME == 'classic' else 10
    
    start = (page - 1) * per_page
    end = start + per_page
    
    articles = articles_by_date[start:end]
    total_pages = (len(articles_by_date) + per_page - 1) // per_page
    
    return render_template('browse.html', 
                         articles=articles,
                         page=page,
                         total_pages=total_pages)


def find_free_port(start_port=5001, max_attempts=100):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_attempts}")


if __name__ == '__main__':
    # If -all provided, spawn six servers (1-6) on successive ports
    if RUN_ALL:
        # Ensure cache exists so children load quickly
        load_or_create_index()
        base_port = PORT_OVERRIDE if PORT_OVERRIDE else find_free_port()
        theme_nums = ['1', '2', '3', '4', '5', '6']
        procs = []
        print("\n" + "="*60)
        print("Starting multiple Wikinews UI servers...")
        for i, num in enumerate(theme_nums):
            port = base_port + i
            cmd = [sys.executable, __file__, num, f"--port={port}"]
            try:
                p = subprocess.Popen(cmd)
                procs.append((num, port, p.pid))
            except Exception as e:
                print(f"Failed to start server {num} on port {port}: {e}")
        for num, port, pid in procs:
            print(f"Server {num} running at http://localhost:{port} (PID {pid})")
        print("="*60 + "\n")
        # Keep parent alive to avoid abrupt exit; wait for children
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
    else:
        # Load or create article index
        load_or_create_index()
        
        # Determine port
        port = PORT_OVERRIDE if PORT_OVERRIDE else find_free_port()
        
        # Run the Flask app
        print("\n" + "="*60)
        print("Wikinews UI is starting...")
        print(f"Open your browser and go to: http://localhost:{port}")
        print("="*60 + "\n")
        
        # Use use_reloader=False to avoid issues with port binding in debug mode
        app.run(debug=True, port=port, use_reloader=False)

