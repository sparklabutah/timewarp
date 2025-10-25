"""
Simple Wikipedia UI - Flask Backend
Parses Wikipedia XML dump and serves articles with a Wikipedia-like UI
OPTIMIZED VERSION with regex-based parsing and HTML pre-caching
"""

import xml.etree.ElementTree as ET
import re
from flask import Flask, render_template, request, jsonify
import pickle
import os
import random
import sys

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Determine theme from command line argument
THEME = 'classic'  # Default theme
if len(sys.argv) > 1:
    if sys.argv[1] == '-1' or sys.argv[1] == 'classic':
        THEME = 'classic'
    elif sys.argv[1] == '-2' or sys.argv[1] == 'modern':
        THEME = 'modern'
    elif sys.argv[1] == '-3' or sys.argv[1] == 'wikipedia2002':
        THEME = 'wikipedia2002'
    elif sys.argv[1] == '-4' or sys.argv[1] == 'wikipedia2001':
        THEME = 'wikipedia2001'

print(f"Using theme: {THEME}")

# Initialize Flask with theme-specific paths
app = Flask(__name__,
            template_folder=os.path.join(SCRIPT_DIR, 'themes', THEME, 'templates'),
            static_folder=os.path.join(SCRIPT_DIR, 'themes', THEME, 'static'))

# Paths relative to the script location
XML_DUMP_PATH = os.path.join(SCRIPT_DIR, 'simplewiki-latest-pages-articles.xml')
INDEX_CACHE_PATH = os.path.join(SCRIPT_DIR, 'wiki_index.pkl')  # Now stores pre-parsed HTML!

# Optional: Limit number of articles for testing (set to None for all)
# TESTING: Set to 1000 for quick testing, None for full indexing
MAX_ARTICLES = None  # Change to 1000 for testing!

# Global index of articles (stores pre-parsed HTML for instant serving!)
article_index = {}


def parse_and_clean_wikitext(wikitext):
    """
    Parse wikitext and return cleaned HTML
    This is used during indexing to pre-process articles
    Uses regex-based approach to avoid wikitextparser mutation issues
    """
    if not wikitext:
        return ""
    
    try:
        # Use regex to remove complex elements BEFORE parsing
        # This is more reliable than mutating parsed objects
        
        # Remove templates (nested and multiline)
        # Keep removing until no more templates found
        prev_len = 0
        while len(wikitext) != prev_len:
            prev_len = len(wikitext)
            # Remove {{...}} carefully handling nesting
            wikitext = re.sub(r'\{\{[^{}]*\}\}', '', wikitext)
        
        # Remove tables {|...|}
        wikitext = re.sub(r'\{\|.*?\|\}', '', wikitext, flags=re.DOTALL)
        
        # Remove HTML comments
        wikitext = re.sub(r'<!--.*?-->', '', wikitext, flags=re.DOTALL)
        
        # Remove category links
        wikitext = re.sub(r'\[\[Category:.*?\]\]', '', wikitext, flags=re.IGNORECASE)
        
        # Remove file/image links
        wikitext = re.sub(r'\[\[(File|Image):.*?\]\]', '', wikitext, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove __NOTOC__, __FORCETOC__, etc.
        wikitext = re.sub(r'__[A-Z]+__', '', wikitext)
        
        # Clean up extra whitespace
        wikitext = re.sub(r'\n\n+', '\n\n', wikitext)
        
        # Convert remaining wikitext to HTML
        html = convert_wikitext_to_html(wikitext)
        
        return html
        
    except Exception as e:
        print(f"Error parsing wikitext: {e}")
        # Fallback: return basic paragraphs
        return '<p>' + '</p><p>'.join(wikitext.split('\n\n')[:10]) + '</p>'


def convert_wikitext_to_html(text):
    """Convert remaining wikitext markup to HTML"""
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
    
    # Use iterparse for memory efficiency with large files
    context = ET.iterparse(XML_DUMP_PATH, events=('start', 'end'))
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
    return render_template('index.html')


@app.route('/wiki/<title>')
def article(title):
    """
    Display a Wikipedia article
    Uses pre-parsed HTML from index - INSTANT serving!
    """
    # Look up article in index (case-insensitive)
    article_data = article_index.get(title.lower())
    
    if not article_data:
        return render_template('404.html', title=title), 404
    
    # Return pre-parsed HTML directly - no parsing needed!
    return render_template('article.html', 
                         title=article_data['title'],
                         content=article_data['html'],
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
        return jsonify({'title': article_index[random_key]['title']})
    return jsonify({'title': None})


if __name__ == '__main__':
    # Load or create article index
    load_or_create_index()
    
    # Run the Flask app
    print("\n" + "="*60)
    print("Simple Wikipedia UI is starting...")
    print("Open your browser and go to: http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)

