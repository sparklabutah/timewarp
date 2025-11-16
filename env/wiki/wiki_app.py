"""
Simple Wikipedia UI - Flask Backend
Parses Wikipedia XML dump and serves articles with a Wikipedia-like UI
OPTIMIZED VERSION with MediaWiki parser and HTML pre-caching
"""

import xml.etree.ElementTree as ET
import re
from html import escape
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for
import json
import pickle
import os
import random
import sys
import mwparserfromhell
import bz2
import socket
import subprocess
import time

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def _parse_args(argv):
    """Parse CLI args for theme selection and optional port override."""
    num_to_theme = {
        '1': '1-2001',
        '2': '2-2002',
        '3': '3-2003-4',
        '4': '4-2005-2022',
        '5': '5-2023-2025',
        '6': '6-minimal',
        '7': 'modern',
    }
    name_aliases = {
        'classic': '6-minimal',
        'minimal': '6-minimal',
        'modern': 'modern',
        '2001': '1-2001',
        '2002': '2-2002',
        '2003': '3-2003-4',
        '2004': '3-2003-4',
        '2005': '4-2005-2022',
        '2022': '4-2005-2022',
        '2023': '5-2023-2025',
        '2025': '5-2023-2025',
        'all': 'all',
    }
    selected_theme = '6-minimal'
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
# Check if theme has subdirectories or flat structure
theme_path = os.path.join(SCRIPT_DIR, 'themes', THEME)
has_templates_subdir = os.path.exists(os.path.join(theme_path, 'templates'))
has_static_subdir = os.path.exists(os.path.join(theme_path, 'static'))

template_folder = os.path.join(theme_path, 'templates') if has_templates_subdir else theme_path
static_folder = os.path.join(theme_path, 'static') if has_static_subdir else theme_path

app = Flask(__name__,
            template_folder=template_folder,
            static_folder=static_folder)

# Paths relative to the script location
XML_DUMP_PATH = os.path.join(SCRIPT_DIR, 'simplewiki-latest-pages-articles.xml.bz2')
INDEX_CACHE_PATH = os.path.join(SCRIPT_DIR, 'wiki_index.pkl')  # Now stores pre-parsed HTML!
LOGOS_DIR = os.path.join(SCRIPT_DIR, 'logos')

# Optional: Limit number of articles for testing (set to None for all)
# TESTING: Set to 1000 for quick testing, None for full indexing
MAX_ARTICLES = None  # Change to 1000 for testing!

# Global index of articles (stores pre-parsed HTML for instant serving!)
article_index = {}


def parse_and_clean_wikitext(wikitext):
    """
    Parse wikitext and return cleaned HTML
    This is used during indexing to pre-process articles
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


def slugify_heading(text):
    """Convert heading text to a URL-friendly slug"""
    # Remove HTML tags first
    text = re.sub(r'<[^>]+>', '', text)
    # Remove markdown formatting (*, _, etc.)
    text = re.sub(r'\*+|_+', '', text)
    # Remove any remaining special characters except spaces, letters, numbers
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with underscores and return
    return text.strip().replace(' ', '_').replace('-', '_')


def convert_wikitext_to_html(text):
    """Convert remaining wikitext markup to HTML"""
    # Helper function to add ID to heading
    def add_heading_id(match, tag):
        heading_text = match.group(1)
        heading_id = slugify_heading(heading_text)
        return f'<{tag} id="{heading_id}">{heading_text}</{tag}>'
    
    # Convert headings with IDs
    text = re.sub(r'^======\s*(.*?)\s*======', lambda m: add_heading_id(m, 'h6'), text, flags=re.MULTILINE)
    text = re.sub(r'^=====\s*(.*?)\s*=====', lambda m: add_heading_id(m, 'h5'), text, flags=re.MULTILINE)
    text = re.sub(r'^====\s*(.*?)\s*====', lambda m: add_heading_id(m, 'h4'), text, flags=re.MULTILINE)
    text = re.sub(r'^===\s*(.*?)\s*===', lambda m: add_heading_id(m, 'h3'), text, flags=re.MULTILINE)
    text = re.sub(r'^==\s*(.*?)\s*==', lambda m: add_heading_id(m, 'h2'), text, flags=re.MULTILINE)
    
    # Convert bold and italic
    text = re.sub(r"'''''(.*?)'''''", r'<strong><em>\1</em></strong>', text)
    text = re.sub(r"'''(.*?)'''", r'<strong>\1</strong>', text)
    text = re.sub(r"''(.*?)''", r'<em>\1</em>', text)
    
    # Convert internal links [[Link]] or [[Link|Display]]
    text = re.sub(r'\[\[([^\|\]]+)\|([^\]]+)\]\]', r'<a href="/wiki/\1">\2</a>', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'<a href="/wiki/\1">\1</a>', text)
    
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


def build_overview_links(html: str):
    """Group anchors under nearest h2/h3 heading from article HTML.
    Returns a list of {'section': str, 'links': [{'href','text'}]}.
    """
    if not html:
        return []
    sections = []
    headings = list(re.finditer(r"<h[23][^>]*>(.*?)</h[23]>", html, flags=re.IGNORECASE | re.DOTALL))
    if not headings:
        links = [
            {'href': m.group(1), 'text': re.sub(r"<[^>]+>", "", m.group(2)).strip()}
            for m in re.finditer(r"<a[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", html, flags=re.IGNORECASE | re.DOTALL)
            if m.group(2).strip()
        ]
        if links:
            sections.append({'section': 'Links', 'links': links})
        return sections
    for i, h in enumerate(headings):
        # Extract heading text and ID
        heading_tag = h.group(0)
        title = re.sub(r"<[^>]+>", "", h.group(1)).strip() or 'Section'
        # Try to extract ID from heading tag
        id_match = re.search(r'id="([^"]+)"', heading_tag)
        if id_match:
            section_id = id_match.group(1)
        else:
            # Fallback: generate slug from title
            section_id = slugify_heading(title)
        start = h.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(html)
        chunk = html[start:end]
        links = []
        for m in re.finditer(r"<a[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", chunk, flags=re.IGNORECASE | re.DOTALL):
            text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if text:
                links.append({'href': m.group(1), 'text': text})
        # Add all sections, even if they don't have links
        sections.append({'section': title, 'section_id': section_id, 'links': links})
    return sections


def split_first_paragraph(html: str):
    """Return (first_paragraph_html, remainder_html)."""
    if not html:
        return None, ""
    m = re.search(r"<p[^>]*>.*?</p>", html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return None, html
    first_para = html[m.start():m.end()]
    remainder = html[m.end():]
    return first_para, remainder


def parse_xml_dump():
    """
    Parse the XML dump and create an index of articles
    PRE-PARSES all wikitext to HTML during indexing for instant serving!
    """
    import time
    
    print("="*70)
    print("Parsing Wikipedia XML dump and converting to HTML...")
    print("This will take longer but makes serving articles INSTANT!")
    if MAX_ARTICLES:
        print(f"TESTING MODE: Limiting to {MAX_ARTICLES} articles")
    else:
        print("FULL MODE: Processing ALL articles (may take 1-2 hours)")
    print("="*70)
    
    # XML namespace
    ns = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
    
    # Open bz2 compressed file and use iterparse for memory efficiency
    with bz2.open(XML_DUMP_PATH, 'rb') as f:
        context = ET.iterparse(f, events=('start', 'end'))
        context = iter(context)
        
        count = 0
        start_time = time.time()
        
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
                    if namespace == '0' and title and len(text) > 0:
                        # SKIP REDIRECT PAGES
                        # Redirects start with #REDIRECT [[Target]] or #redirect [[Target]]
                        if text.strip().upper().startswith('#REDIRECT'):
                            # Skip this page - it's a redirect, not actual content
                            elem.clear()
                            continue
                        
                        # PRE-PARSE: Convert wikitext to HTML now!
                        html_content = parse_and_clean_wikitext(text)
                        
                        # Store title, pre-parsed HTML, and timestamp
                        article_index[title.lower()] = {
                            'title': title,
                            'html': html_content,
                            'timestamp': timestamp
                        }
                        count += 1
                        
                        # Progress reporting with time estimates
                        if count % 100 == 0:
                            elapsed = time.time() - start_time
                            rate = count / elapsed
                            print(f"Parsed {count} articles ({rate:.1f} articles/sec, {elapsed:.1f}s elapsed)")
                        
                        # Check if we've hit the limit
                        if MAX_ARTICLES and count >= MAX_ARTICLES:
                            print(f"\nReached limit of {MAX_ARTICLES} articles - stopping early")
                            break
                
                # Clear element to free memory
                elem.clear()
    
    elapsed = time.time() - start_time
    print("="*70)
    print(f"Indexing complete! Total articles indexed: {count}")
    print(f"Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"Average speed: {count/elapsed:.1f} articles/second")
    print("="*70)
    
    # Save index to cache
    print("Saving index to cache...")
    with open(INDEX_CACHE_PATH, 'wb') as f:
        pickle.dump(article_index, f)
    
    cache_size_mb = os.path.getsize(INDEX_CACHE_PATH) / (1024 * 1024)
    print(f"Cache saved to {INDEX_CACHE_PATH} ({cache_size_mb:.1f} MB)")
    
    return article_index


def load_or_create_index():
    """Load cached index or create new one"""
    global article_index
    
    if os.path.exists(INDEX_CACHE_PATH):
        print("Loading cached index...")
        with open(INDEX_CACHE_PATH, 'rb') as f:
            article_index = pickle.load(f)
        print(f"Loaded {len(article_index)} articles from cache")
    else:
        article_index = parse_xml_dump()
    
    return article_index


# NOTE: These functions are no longer needed because we pre-parse during indexing!
# Keeping them commented out for reference:
#
# def get_article_from_xml(title):
#     """DEPRECATED - Articles are now pre-parsed in the index"""
#     pass
#
# def wikitext_to_html(wikitext):
#     """DEPRECATED - Now using parse_and_clean_wikitext() during indexing"""
#     pass


@app.route('/')
def index():
    """Main page with search"""
    # Check if there's a search query
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        # Try to find the article
        search_lower = search_query.lower()
        article_data = article_index.get(search_lower)
        
        if article_data:
            # Article found, redirect to article page
            # Convert spaces to underscores for URL (Wikipedia convention)
            url_title = article_data['title'].replace(' ', '_')
            return redirect(url_for('article', title=url_title))
        else:
            # Article not found, show search results/404 page
            return render_template('404.html', query=search_query, title=search_query), 404
    
    # No search query, show main page
    return render_template('index.html')


@app.route('/wiki/<title>')
def article(title):
    """
    Display a Wikipedia article
    Uses pre-parsed HTML from index - INSTANT serving!
    """
    # URL decode and normalize: replace underscores with spaces (Wikipedia convention)
    from urllib.parse import unquote
    title = unquote(title)  # Handle URL encoding like %20
    title_normalized = title.replace('_', ' ')  # Replace underscores with spaces
    
    # Look up article in index (case-insensitive)
    article_data = article_index.get(title_normalized.lower())
    
    if not article_data:
        return render_template('404.html', query=title, title=title), 404
    
    # Return pre-parsed HTML directly - no parsing needed!
    overview_links = build_overview_links(article_data['html'])
    first_paragraph_html, remainder_html = split_first_paragraph(article_data['html'])
    
    return render_template('article.html', 
                         title=article_data['title'],
                         content=article_data['html'],
                         first_paragraph_html=first_paragraph_html,
                         remainder_html=remainder_html,
                         overview_links=overview_links,
                         timestamp=article_data.get('timestamp', ''))


@app.route('/search')
def search():
    """Search for articles"""
    query = request.args.get('q', '').lower().strip()
    
    if not query:
        return jsonify([])
    
    # Search in article index
    results = []
    for key, data in article_index.items():
        if query in key:
            results.append({
                'title': data['title']
            })
            
            if len(results) >= 20:  # Limit results
                break
    
    return jsonify(results)


@app.route('/random')
def random_article():
    """Get a random article"""
    if article_index:
        random_key = random.choice(list(article_index.keys()))
        title = article_index[random_key]['title']
        # Convert spaces to underscores for URL (Wikipedia convention)
        url_title = title.replace(' ', '_')
        # Redirect to the random article page
        return redirect(url_for('article', title=url_title))
    # If no articles, redirect to home
    return redirect(url_for('index'))


@app.route('/logos/<path:filename>')
def logos(filename):
    """Serve logo and shared image assets from env/simplewiki/logos"""
    return send_from_directory(LOGOS_DIR, filename)


@app.route('/theme_assets/<path:filename>')
def theme_assets(filename):
    """Serve assets located under the active theme's assets directory."""
    assets_dir = os.path.join(SCRIPT_DIR, 'themes', THEME, 'assets')
    return send_from_directory(assets_dir, filename)


@app.route('/overview/<topic>')
def overview(topic):
    """Render an overview page for a topic using 2002 theme structure.
    Looks for JSON at themes/<THEME>/overviews/<topic>.json
    """
    overviews_dir = os.path.join(SCRIPT_DIR, 'themes', THEME, 'overviews')
    json_path = os.path.join(overviews_dir, f'{topic}.json')
    if not os.path.exists(json_path):
        return render_template('404.html', title=f'Overview: {topic}'), 404
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return render_template('404.html', title=f'Overview: {topic}'), 404

    title = data.get('title', f'Overview of {topic.title()}')
    sections = data.get('sections', [])
    return render_template('overview.html', title=title, sections=sections)


def find_free_port(start_port=5000, max_attempts=100):
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
        theme_nums = ['1', '2', '3', '4', '5', '6']  # exclude 7 (modern)
        procs = []
        print("\n" + "="*60)
        print("Starting multiple Simple Wikipedia UI servers...")
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
        print("Simple Wikipedia UI is starting...")
        print(f"Open your browser and go to: http://localhost:{port}")
        print("="*60 + "\n")
        
        # Use use_reloader=False to avoid issues with port binding in debug mode
        app.run(debug=True, port=port, use_reloader=False)

