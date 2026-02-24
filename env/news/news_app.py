"""
Wikinews UI - Flask Backend
Parses Wikinews XML dump and serves news articles with a modern news UI
Uses mwparserfromhell for proper MediaWiki parsing and HTML pre-caching
Features BM25-based search engine with inverted index for fast, relevant results
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
import math
from collections import defaultdict
from dotenv import load_dotenv


# =============================================================================
# BM25 Search Engine with Inverted Index
# =============================================================================

class NewsSearchEngine:
    """
    BM25-based search engine with inverted index for fast news article search.
    
    Features:
    - BM25 ranking algorithm (superior to TF-IDF)
    - Inverted index for O(1) term lookups
    - Field boosting (title > category > content)
    - Basic stemming for better recall
    - Query term coverage bonuses
    - LRU cache for repeated queries
    """
    
    # BM25 parameters
    K1 = 1.5  # Term frequency saturation (typically 1.2-2.0)
    B = 0.75  # Length normalization (0 = no normalization, 1 = full normalization)
    
    # Field weight multipliers
    FIELD_WEIGHTS = {
        'title': 10.0,      # Title matches are most important
        'category': 5.0,    # Category matches are moderately important
        'content': 1.0      # Content matches are baseline
    }
    
    # Common English stop words to skip during indexing
    STOP_WORDS = frozenset([
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'were', 'will', 'with', 'the', 'this', 'but', 'they',
        'have', 'had', 'what', 'when', 'where', 'who', 'which', 'why', 'how'
    ])
    
    def __init__(self):
        # Inverted index: term -> {doc_key -> {field -> term_frequency}}
        self.inverted_index = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
        # Document field lengths for BM25 normalization
        self.doc_field_lengths = defaultdict(lambda: defaultdict(int))
        
        # Document frequency: term -> number of documents containing term
        self.doc_freq = defaultdict(int)
        
        # Average field lengths (computed after indexing)
        self.avg_field_lengths = defaultdict(float)
        
        # Total document count
        self.total_docs = 0
        
        # Set of all indexed document keys
        self.indexed_docs = set()
        
        # Search result cache
        self._search_cache = {}
        self._cache_max_size = 1000
    
    def _strip_html(self, html):
        """Remove HTML tags and decode entities to get plain text."""
        if not html:
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Decode common HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#39;', "'")
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _stem(self, word):
        """
        Basic Porter-style stemmer for improved recall.
        Handles common English suffixes.
        """
        if len(word) <= 3:
            return word
        
        # Handle common suffixes in order of length (longest first)
        suffix_rules = [
            ('ational', 'ate'), ('tional', 'tion'), ('ization', 'ize'),
            ('fulness', 'ful'), ('ousness', 'ous'), ('iveness', 'ive'),
            ('ement', ''), ('ment', ''), ('ness', ''), ('ance', ''),
            ('ence', ''), ('able', ''), ('ible', ''), ('tion', ''),
            ('sion', ''), ('ally', ''), ('ful', ''), ('ous', ''),
            ('ive', ''), ('ize', ''), ('ing', ''), ('ies', 'y'),
            ('es', ''), ('ed', ''), ('ly', ''), ('er', ''), ('s', '')
        ]
        
        for suffix, replacement in suffix_rules:
            if word.endswith(suffix) and len(word) - len(suffix) + len(replacement) >= 3:
                return word[:-len(suffix)] + replacement
        
        return word
    
    def tokenize(self, text, apply_stemming=True):
        """
        Tokenize text into normalized terms.
        
        Args:
            text: Raw text to tokenize
            apply_stemming: Whether to apply stemming
            
        Returns:
            List of tokens (may contain duplicates for term frequency)
        """
        if not text:
            return []
        
        # Extract alphanumeric words (handles hyphenated words better)
        words = re.findall(r'\b[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\b', text.lower())
        
        # Process tokens
        tokens = []
        for word in words:
            # Skip very short words and stop words
            if len(word) < 2 or word in self.STOP_WORDS:
                continue
            
            # Handle hyphenated words: index both full and parts
            if '-' in word:
                parts = word.split('-')
                for part in parts:
                    if len(part) >= 2 and part not in self.STOP_WORDS:
                        token = self._stem(part) if apply_stemming else part
                        tokens.append(token)
                # Also index the full hyphenated form
                tokens.append(word)
            else:
                token = self._stem(word) if apply_stemming else word
                tokens.append(token)
        
        return tokens
    
    def index_document(self, doc_key, title, html_content, categories):
        """
        Index a document for searching.
        
        Args:
            doc_key: Unique document identifier (lowercase title)
            title: Article title
            html_content: HTML content of the article
            categories: List of category strings
        """
        if doc_key in self.indexed_docs:
            return  # Already indexed
        
        self.indexed_docs.add(doc_key)
        self.total_docs += 1
        
        # Tokenize each field
        title_tokens = self.tokenize(title)
        content_text = self._strip_html(html_content)
        content_tokens = self.tokenize(content_text)
        category_text = ' '.join(categories) if categories else ''
        category_tokens = self.tokenize(category_text)
        
        # Store field lengths for BM25 normalization
        self.doc_field_lengths[doc_key]['title'] = len(title_tokens)
        self.doc_field_lengths[doc_key]['content'] = len(content_tokens)
        self.doc_field_lengths[doc_key]['category'] = len(category_tokens)
        
        # Track which terms appear in this document (for document frequency)
        doc_terms = set()
        
        # Index title tokens
        for token in title_tokens:
            self.inverted_index[token][doc_key]['title'] += 1
            doc_terms.add(token)
        
        # Index content tokens
        for token in content_tokens:
            self.inverted_index[token][doc_key]['content'] += 1
            doc_terms.add(token)
        
        # Index category tokens
        for token in category_tokens:
            self.inverted_index[token][doc_key]['category'] += 1
            doc_terms.add(token)
        
        # Update document frequency for each unique term
        for term in doc_terms:
            self.doc_freq[term] += 1
    
    def finalize_index(self):
        """
        Finalize the index after all documents are indexed.
        Computes average field lengths for BM25 normalization.
        """
        if self.total_docs == 0:
            return
        
        # Calculate average field lengths
        for field in ['title', 'content', 'category']:
            total_length = sum(
                self.doc_field_lengths[doc][field] 
                for doc in self.indexed_docs
            )
            self.avg_field_lengths[field] = total_length / self.total_docs
        
        # Clear search cache when index changes
        self._search_cache.clear()
        
        print(f"Search index finalized: {self.total_docs} documents, "
              f"{len(self.inverted_index)} unique terms")
    
    def _bm25_score(self, term, doc_key, field):
        """
        Calculate BM25 score for a term in a specific field of a document.
        
        BM25 formula:
        score = IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl/avgdl))
        
        Where:
        - IDF = log((N - n + 0.5) / (n + 0.5) + 1)
        - tf = term frequency in document
        - dl = document length
        - avgdl = average document length
        - k1, b = tuning parameters
        """
        # Term frequency in this field
        tf = self.inverted_index[term][doc_key].get(field, 0)
        if tf == 0:
            return 0.0
        
        # Document frequency (number of docs containing this term)
        n = self.doc_freq.get(term, 0)
        if n == 0:
            return 0.0
        
        # IDF with smoothing (BM25 variant)
        idf = math.log((self.total_docs - n + 0.5) / (n + 0.5) + 1)
        
        # Document length and average length for this field
        dl = self.doc_field_lengths[doc_key].get(field, 1)
        avgdl = self.avg_field_lengths.get(field, 1)
        if avgdl == 0:
            avgdl = 1
        
        # BM25 term frequency component with length normalization
        tf_component = (tf * (self.K1 + 1)) / (
            tf + self.K1 * (1 - self.B + self.B * dl / avgdl)
        )
        
        # Apply field weight
        field_weight = self.FIELD_WEIGHTS.get(field, 1.0)
        
        return idf * tf_component * field_weight
    
    def search(self, query, article_index, max_results=500):
        """
        Search for articles matching the query using BM25 ranking.
        
        Args:
            query: Search query string
            article_index: Dictionary mapping doc_key to article data
            max_results: Maximum number of results to return
            
        Returns:
            List of result dictionaries sorted by relevance
        """
        query = query.strip()
        if not query:
            return []
        
        # Check cache
        cache_key = query.lower()
        if cache_key in self._search_cache:
            return self._search_cache[cache_key][:max_results]
        
        # Tokenize query
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []
        
        # Also try matching exact phrases in title (important for news)
        query_lower = query.lower()
        
        # Calculate BM25 scores for each document
        doc_scores = defaultdict(float)
        doc_matched_terms = defaultdict(set)
        doc_field_matches = defaultdict(set)
        
        # Score each query term
        for term in query_tokens:
            if term not in self.inverted_index:
                continue
            
            # Score documents containing this term
            for doc_key in self.inverted_index[term]:
                for field in ['title', 'content', 'category']:
                    score = self._bm25_score(term, doc_key, field)
                    if score > 0:
                        doc_scores[doc_key] += score
                        doc_matched_terms[doc_key].add(term)
                        doc_field_matches[doc_key].add(field)
        
        # Boost for exact phrase match in title
        for doc_key in doc_scores:
            if doc_key in article_index:
                title = article_index[doc_key].get('title', '').lower()
                if query_lower in title:
                    doc_scores[doc_key] *= 2.0  # Double score for exact title match
        
        # Apply query coverage bonus/penalty
        query_term_set = set(query_tokens)
        num_query_terms = len(query_term_set)
        
        for doc_key in list(doc_scores.keys()):
            matched_count = len(doc_matched_terms[doc_key])
            coverage = matched_count / num_query_terms if num_query_terms > 0 else 0
            
            # Bonus for matching all terms
            if coverage == 1.0:
                doc_scores[doc_key] *= 1.5
            # Small penalty for partial matches (but still include them)
            elif coverage < 0.5:
                doc_scores[doc_key] *= (0.5 + coverage)
        
        # Build result list
        results = []
        for doc_key, score in doc_scores.items():
            if doc_key not in article_index:
                continue
            
            data = article_index[doc_key]
            date_obj = data.get('date')
            
            results.append({
                'title': data.get('title', ''),
                'date': date_obj.strftime('%Y-%m-%d') if date_obj else '',
                'date_obj': date_obj,
                'score': score,
                'matched_terms': len(doc_matched_terms[doc_key]),
                'total_terms': num_query_terms,
                'matched_fields': list(doc_field_matches[doc_key]),
                'categories': data.get('categories', [])
            })
        
        # Sort by score (descending), then by date (newest first)
        results.sort(key=lambda x: (
            -x['score'],
            -(x['date_obj'].timestamp() if x.get('date_obj') else 0)
        ))
        
        # Cache results (limit cache size)
        if len(self._search_cache) >= self._cache_max_size:
            # Remove oldest entries (simple FIFO for now)
            oldest_keys = list(self._search_cache.keys())[:100]
            for key in oldest_keys:
                del self._search_cache[key]
        
        self._search_cache[cache_key] = results
        
        return results[:max_results]
    
    def get_index_stats(self):
        """Return statistics about the search index."""
        return {
            'total_documents': self.total_docs,
            'unique_terms': len(self.inverted_index),
            'avg_title_length': self.avg_field_lengths.get('title', 0),
            'avg_content_length': self.avg_field_lengths.get('content', 0),
            'avg_category_length': self.avg_field_lengths.get('category', 0),
            'cache_size': len(self._search_cache)
        }
    
    def to_dict(self):
        """
        Serialize the search engine to a pickle-safe dictionary.
        Converts nested defaultdicts to regular dicts.
        """
        # Deep convert inverted_index: term -> {doc_key -> {field -> count}}
        inverted_index_serialized = {}
        for term, doc_dict in self.inverted_index.items():
            inverted_index_serialized[term] = {}
            for doc_key, field_dict in doc_dict.items():
                inverted_index_serialized[term][doc_key] = dict(field_dict)
        
        # Deep convert doc_field_lengths: doc_key -> {field -> length}
        doc_field_lengths_serialized = {}
        for doc_key, field_dict in self.doc_field_lengths.items():
            doc_field_lengths_serialized[doc_key] = dict(field_dict)
        
        return {
            'inverted_index': inverted_index_serialized,
            'doc_field_lengths': doc_field_lengths_serialized,
            'doc_freq': dict(self.doc_freq),
            'avg_field_lengths': dict(self.avg_field_lengths),
            'total_docs': self.total_docs,
            'indexed_docs': self.indexed_docs
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Deserialize a search engine from a dictionary.
        Restores nested defaultdict structure.
        """
        engine = cls()
        
        # Restore inverted index
        for term, doc_dict in data.get('inverted_index', {}).items():
            for doc_key, field_dict in doc_dict.items():
                for field, count in field_dict.items():
                    engine.inverted_index[term][doc_key][field] = count
        
        # Restore document field lengths
        for doc_key, field_dict in data.get('doc_field_lengths', {}).items():
            for field, length in field_dict.items():
                engine.doc_field_lengths[doc_key][field] = length
        
        # Restore other data
        engine.doc_freq = defaultdict(int, data.get('doc_freq', {}))
        engine.avg_field_lengths = defaultdict(float, data.get('avg_field_lengths', {}))
        engine.total_docs = data.get('total_docs', 0)
        engine.indexed_docs = data.get('indexed_docs', set())
        
        return engine


# Global search engine instance
search_engine = NewsSearchEngine()

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
    """Parse the Wikinews XML dump and create an index with BM25 search support"""
    import bz2
    
    global search_engine
    
    print("="*70)
    print("Parsing Wikinews XML dump and building BM25 search index...")
    if MAX_ARTICLES:
        print(f"TESTING MODE: Limiting to {MAX_ARTICLES} articles")
    else:
        print("FULL MODE: Processing ALL articles")
    print("="*70)
    
    # Reset search engine for fresh indexing
    search_engine = NewsSearchEngine()
    
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
                        
                        # Store in article index
                        doc_key = title.lower()
                        article_index[doc_key] = article_data
                        articles_list.append(article_data)
                        
                        # Index in search engine for BM25 search
                        search_engine.index_document(
                            doc_key=doc_key,
                            title=title,
                            html_content=html_content,
                            categories=categories
                        )
                        
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
    
    # Finalize search index (compute average lengths for BM25)
    search_engine.finalize_index()
    
    elapsed = time.time() - start_time
    print("="*70)
    print(f"Indexing complete! Total articles: {count}")
    print(f"Total time: {elapsed:.1f} seconds")
    stats = search_engine.get_index_stats()
    print(f"Search index: {stats['unique_terms']} unique terms")
    print("="*70)
    
    # Sort articles by date (newest first)
    articles_list.sort(key=lambda x: x['date'], reverse=True)
    
    # Save index to cache (including search engine data)
    print("Saving index and search engine to cache...")
    cache_data = {
        'index': article_index,
        'by_date': articles_list,
        'search_engine': search_engine.to_dict()
    }
    with open(INDEX_CACHE_PATH, 'wb') as f:
        # Use protocol 4 for better compatibility across Python versions
        pickle.dump(cache_data, f, protocol=4)
    
    cache_size_mb = os.path.getsize(INDEX_CACHE_PATH) / (1024 * 1024)
    print(f"Cache saved ({cache_size_mb:.1f} MB)")
    
    return article_index, articles_list


def load_or_create_index():
    """Load cached index or create new one, including BM25 search engine"""
    global article_index, articles_by_date, search_engine
    
    if os.path.exists(INDEX_CACHE_PATH):
        print("Loading cached index...")
        try:
            with open(INDEX_CACHE_PATH, 'rb') as f:
                cache_data = pickle.load(f)
            article_index = cache_data['index']
            articles_by_date = cache_data['by_date']
            
            # Load search engine data if available
            if 'search_engine' in cache_data:
                search_engine = NewsSearchEngine.from_dict(cache_data['search_engine'])
                
                print(f"Loaded {len(article_index)} articles from cache")
                stats = search_engine.get_index_stats()
                print(f"Search index restored: {stats['unique_terms']} terms, {stats['total_documents']} docs")
            else:
                # Old cache format without search engine - rebuild search index
                print("Cache missing search index. Rebuilding search index...")
                search_engine = NewsSearchEngine()
                for doc_key, data in article_index.items():
                    search_engine.index_document(
                        doc_key=doc_key,
                        title=data.get('title', ''),
                        html_content=data.get('html', ''),
                        categories=data.get('categories', [])
                    )
                search_engine.finalize_index()
                
                # Update cache with search engine data
                cache_data['search_engine'] = search_engine.to_dict()
                with open(INDEX_CACHE_PATH, 'wb') as f:
                    pickle.dump(cache_data, f, protocol=4)
                print("Updated cache with search index")
                
        except (UnicodeDecodeError, pickle.UnpicklingError, EOFError, KeyError) as e:
            print(f"Error loading cache: {e}")
            print("Cache file appears corrupted or incompatible. Regenerating index...")
            # Remove corrupted cache file
            try:
                os.remove(INDEX_CACHE_PATH)
            except:
                pass
            article_index, articles_by_date = parse_xml_dump()
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


@app.route('/search')
def search():
    """
    Search for articles using BM25 ranking algorithm.
    
    Searches in title, content, and categories with proper relevance ranking.
    Features:
    - BM25 scoring with field boosting
    - Stemming for better recall
    - Query term coverage bonuses
    - Result caching for performance
    """
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
    
    # Use BM25 search engine
    all_results = search_engine.search(query, article_index, max_results=1000)
    
    if not all_results:
        if is_ajax:
            return jsonify([])
        return render_template('search.html', 
                             query=query, 
                             results=[],
                             page=1,
                             total_pages=0,
                             total_results=0,
                             theme=THEME)
    
    # Calculate pagination
    total_results = len(all_results)
    total_pages = (total_results + per_page - 1) // per_page
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages))
    
    # Get results for current page
    start = (page - 1) * per_page
    end = start + per_page
    page_results = all_results[start:end]
    
    # Debug output with search quality metrics
    if page_results:
        avg_coverage = sum(r['matched_terms'] / r['total_terms'] for r in page_results) / len(page_results)
        print(f"Search: '{query}' | Total: {total_results} | Page: {page}/{total_pages} | "
              f"Avg term coverage: {avg_coverage:.1%}")
    else:
        print(f"Search: '{query}' | No results")
    
    # Clean up results for response (remove internal scoring data)
    cleaned_results = []
    for result in page_results:
        cleaned_results.append({
            'title': result['title'],
            'date': result['date'],
            'categories': result.get('categories', [])
        })
    
    # Return JSON for AJAX requests
    if is_ajax:
        return jsonify(cleaned_results)
    
    # Return HTML page for direct navigation
    return render_template('search.html', 
                         query=query, 
                         results=cleaned_results,
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


@app.route('/search/stats')
def search_stats():
    """Return search engine statistics (for debugging/monitoring)"""
    stats = search_engine.get_index_stats()
    stats['articles_count'] = len(article_index)
    return jsonify(stats)


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


def find_free_ports(count=6, start_port=5001, max_attempts=100):
    """Find multiple sequential free ports starting from start_port"""
    ports = []
    current_port = start_port
    attempts = 0
    
    while len(ports) < count and attempts < max_attempts:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', current_port))
                ports.append(current_port)
                current_port += 1
        except OSError:
            # Port is in use, try next port
            current_port += 1
        attempts += 1
    
    if len(ports) < count:
        raise RuntimeError(f"Could not find {count} free ports in range {start_port}-{start_port + max_attempts}")
    
    return ports


if __name__ == '__main__':
    # If -all provided, spawn six servers (1-6) on successive ports
    if RUN_ALL:
        # Ensure cache exists so children load quickly
        load_or_create_index()
        # Find sequential free ports
        if PORT_OVERRIDE:
            # If port override provided, start from that port and find sequential ports
            ports = find_free_ports(count=6, start_port=PORT_OVERRIDE)
        else:
            # Start from 5001 and find sequential free ports
            ports = find_free_ports(count=6, start_port=5001)
        theme_nums = ['1', '2', '3', '4', '5', '6']
        procs = []
        print("\n" + "="*60)
        print("Starting multiple Wikinews UI servers...")
        for i, num in enumerate(theme_nums):
            port = ports[i]
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
        
        # Determine port - use find_free_port to ensure it's actually free
        port = PORT_OVERRIDE if PORT_OVERRIDE else find_free_port()
        
        # Run the Flask app
        print("\n" + "="*60)
        print("Wikinews UI is starting...")
        print(f"Open your browser and go to: http://localhost:{port}")
        print("="*60 + "\n")
        
        # Use use_reloader=False to avoid issues with port binding in debug mode
        app.run(debug=True, port=port, use_reloader=False)

