"""
Wikinews UI - Flask Backend
Parses Wikinews XML dump and serves news articles with a modern news UI
"""

import xml.etree.ElementTree as ET
import re
from flask import Flask, render_template, request, jsonify
import pickle
import os
import random
from datetime import datetime

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize Flask
app = Flask(__name__,
            template_folder=os.path.join(SCRIPT_DIR, 'templates'),
            static_folder=os.path.join(SCRIPT_DIR, 'static'))

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
    """Parse wikitext and return cleaned HTML for news articles"""
    if not wikitext:
        return ""
    
    try:
        # Remove templates (keep doing until no more templates)
        prev_len = 0
        while len(wikitext) != prev_len:
            prev_len = len(wikitext)
            wikitext = re.sub(r'\{\{[^{}]*\}\}', '', wikitext)
        
        # Remove tables
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
        
        # Convert to HTML
        html = convert_wikitext_to_html(wikitext)
        
        return html
        
    except Exception as e:
        print(f"Error parsing wikitext: {e}")
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
    
    # Convert internal links [[Link]] or [[Link|Display]]
    text = re.sub(r'\[\[([^\|\]]+)\|([^\]]+)\]\]', r'<a href="/news/\1">\2</a>', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'<a href="/news/\1">\1</a>', text)
    
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
                'title': data['title'],
                'date': data['date'].strftime('%Y-%m-%d') if data.get('date') else ''
            })
            
            if len(results) >= 20:
                break
    
    return jsonify(results)


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
    per_page = 50
    
    start = (page - 1) * per_page
    end = start + per_page
    
    articles = articles_by_date[start:end]
    total_pages = (len(articles_by_date) + per_page - 1) // per_page
    
    return render_template('browse.html', 
                         articles=articles,
                         page=page,
                         total_pages=total_pages)


if __name__ == '__main__':
    # Load or create article index
    load_or_create_index()
    
    # Run the Flask app
    print("\n" + "="*60)
    print("Wikinews UI is starting...")
    print("Open your browser and go to: http://localhost:5001")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5001)

