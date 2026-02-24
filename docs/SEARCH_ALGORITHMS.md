# TimeWarp Search Algorithms: Technical Documentation

This document provides an in-depth technical overview of the search algorithms implemented across the three TimeWarp web environments: **Wikipedia**, **Wikinews**, and **WebShop**.

---

## Table of Contents

1. [Overview](#overview)
2. [Wikipedia Search](#wikipedia-search)
3. [Wikinews Search (BM25)](#wikinews-search-bm25)
4. [WebShop Search (Lucene/Pyserini)](#webshop-search-lucenepyserini)
5. [Algorithm Comparison](#algorithm-comparison)
6. [Performance Considerations](#performance-considerations)

---

## Overview

| Environment | Algorithm | Index Type | Content Searched | Complexity |
|-------------|-----------|------------|------------------|------------|
| Wikipedia | Substring Matching | None (linear scan) | Title only | O(n) |
| Wikinews | BM25 with Inverted Index | Inverted Index | Title, Content, Categories | O(k) per term |
| WebShop | Lucene BM25 | Lucene Index | Product metadata | O(log n) |

---

## Wikipedia Search

### Implementation Location
`env/wiki/wiki_app.py` - `/search` route

### Algorithm: Simple Substring Matching

The Wikipedia search uses the simplest possible search approach: linear substring matching on article titles.

### How It Works

```python
def search():
    query = request.args.get('q', '').lower().strip()
    
    results = []
    for key, data in article_index.items():
        if query in key:  # Substring match on lowercase title
            results.append({'title': data['title']})
            if len(results) >= 20:
                break
    
    return jsonify(results)
```

### Algorithm Details

**Input:** Query string `q`

**Process:**
1. Convert query to lowercase
2. Iterate through all article keys (lowercase titles)
3. Check if query is a substring: `query in key`
4. Return first 20 matches

**Time Complexity:** \( O(n \cdot m) \)

Where:
- \( n \) = number of articles in index
- \( m \) = average title length (for substring comparison)

### Mathematical Model

For a query \( q \) and document title \( t \):

\[
\text{match}(q, t) = 
\begin{cases} 
1 & \text{if } q \subseteq t \\
0 & \text{otherwise}
\end{cases}
\]

Where \( q \subseteq t \) denotes that \( q \) is a substring of \( t \).

### Limitations

1. **No relevance ranking** - Results are returned in arbitrary order
2. **Title-only search** - Cannot find articles by content
3. **No stemming** - "elections" won't match "election"
4. **No fuzzy matching** - Typos return no results
5. **Linear complexity** - Scales poorly with dataset size

### Use Case Justification

The simple approach is sufficient for Wikipedia because:
- Users typically know article titles
- SimpleWikipedia has a manageable number of articles (~200K)
- Primary navigation is through hyperlinks, not search

---

## Wikinews Search (BM25)

### Implementation Location
`env/news/news_app.py` - `NewsSearchEngine` class

### Algorithm: BM25 (Best Matching 25) with Inverted Index

BM25 is a probabilistic ranking function used by search engines to rank documents based on query terms. It's an improvement over TF-IDF that addresses term frequency saturation and document length normalization.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     NewsSearchEngine                             │
├─────────────────────────────────────────────────────────────────┤
│  Inverted Index                                                  │
│  ┌─────────┬──────────────────────────────────────────────────┐ │
│  │  Term   │  Postings: {doc_key → {field → term_frequency}}  │ │
│  ├─────────┼──────────────────────────────────────────────────┤ │
│  │ "elect" │ {"article1": {"title": 2, "content": 5}}         │ │
│  │ "vote"  │ {"article1": {"content": 3}, "article2": {...}}  │ │
│  └─────────┴──────────────────────────────────────────────────┘ │
│                                                                  │
│  Document Metadata                                               │
│  • Field lengths per document                                    │
│  • Average field lengths (for normalization)                     │
│  • Document frequency per term                                   │
└─────────────────────────────────────────────────────────────────┘
```

### BM25 Mathematical Formula

For a query \( Q \) containing terms \( q_1, q_2, ..., q_n \), the BM25 score for document \( D \) is:

\[
\text{score}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}
\]

Where:
- \( f(q_i, D) \) = frequency of term \( q_i \) in document \( D \)
- \( |D| \) = length of document \( D \) (in terms)
- \( \text{avgdl} \) = average document length across the corpus
- \( k_1 \) = term frequency saturation parameter (default: 1.5)
- \( b \) = length normalization parameter (default: 0.75)

### IDF (Inverse Document Frequency) Calculation

\[
\text{IDF}(q_i) = \ln\left(\frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1\right)
\]

Where:
- \( N \) = total number of documents in the corpus
- \( n(q_i) \) = number of documents containing term \( q_i \)

### Field Boosting

The implementation extends BM25 with field-specific weights:

\[
\text{score}_{\text{field}}(D, Q) = \sum_{i=1}^{n} w_f \cdot \text{BM25}(q_i, D, f)
\]

Where \( w_f \) is the field weight:

| Field | Weight (\( w_f \)) | Rationale |
|-------|-------------------|-----------|
| Title | 10.0 | Highest relevance signal |
| Category | 5.0 | Strong topical indicator |
| Content | 1.0 | Baseline (body text) |

### Stemming Algorithm

A simplified Porter-style stemmer is used to normalize terms:

```python
SUFFIX_RULES = [
    ('ational', 'ate'), ('tional', 'tion'), ('ization', 'ize'),
    ('fulness', 'ful'), ('ousness', 'ous'), ('iveness', 'ive'),
    ('ement', ''), ('ment', ''), ('ness', ''), ('ance', ''),
    ('ence', ''), ('able', ''), ('ible', ''), ('tion', ''),
    ('sion', ''), ('ally', ''), ('ful', ''), ('ous', ''),
    ('ive', ''), ('ize', ''), ('ing', ''), ('ies', 'y'),
    ('es', ''), ('ed', ''), ('ly', ''), ('er', ''), ('s', '')
]
```

**Example transformations:**
- "elections" → "elect"
- "running" → "run"
- "beautiful" → "beauti"

### Query Processing Pipeline

```
User Query: "climate change summit 2024"
         │
         ▼
┌─────────────────────────────────────┐
│ 1. Tokenization                      │
│    ["climate", "change", "summit",   │
│     "2024"]                          │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 2. Stop Word Removal                 │
│    (removes: a, the, is, are, etc.) │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 3. Stemming                          │
│    ["climat", "chang", "summit",     │
│     "2024"]                          │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 4. Inverted Index Lookup             │
│    O(1) per term                     │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 5. BM25 Scoring                      │
│    Calculate score for each doc      │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 6. Query Coverage Boost              │
│    +50% for all terms matched        │
│    Penalty for partial matches       │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ 7. Sort by Score, then Date          │
└─────────────────────────────────────┘
```

### Query Coverage Adjustment

Documents matching all query terms receive a bonus:

\[
\text{final\_score}(D, Q) = \text{score}(D, Q) \times 
\begin{cases} 
1.5 & \text{if coverage} = 1.0 \\
0.5 + 0.5 \times \text{coverage} & \text{otherwise}
\end{cases}
\]

Where:

\[
\text{coverage} = \frac{|\text{matched\_terms}|}{|\text{query\_terms}|}
\]

### Time Complexity Analysis

**Indexing Phase:**
- Per document: \( O(L) \) where \( L \) = document length in tokens
- Total: \( O(N \cdot \bar{L}) \) where \( N \) = number of documents

**Search Phase:**
- Index lookup: \( O(|Q|) \) where \( |Q| \) = number of query terms
- Scoring: \( O(|Q| \cdot D_q) \) where \( D_q \) = documents containing query terms
- Sorting: \( O(D_q \log D_q) \)

**Overall Search:** \( O(|Q| \cdot D_q + D_q \log D_q) \)

### Caching Strategy

Results are cached using an LRU (Least Recently Used) strategy:

```python
_search_cache = {}  # query → results
_cache_max_size = 1000

# On cache overflow, remove oldest 100 entries
if len(_search_cache) >= _cache_max_size:
    oldest_keys = list(_search_cache.keys())[:100]
    for key in oldest_keys:
        del _search_cache[key]
```

---

## WebShop Search (Lucene/Pyserini)

### Implementation Location
`env/webshop/web_agent_site/engine/engine.py`

### Algorithm: Apache Lucene with BM25

WebShop uses **Pyserini**, a Python wrapper for Anserini (which wraps Apache Lucene), providing industrial-strength search capabilities.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Pyserini/Lucene                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌───────────────────────────────────────┐  │
│  │ LuceneSearcher│───▶│ Pre-built Lucene Index                │  │
│  └──────────────┘    │ (indexes/, indexes_1k, indexes_100k)  │  │
│         │            └───────────────────────────────────────┘  │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ search(query, k=50)                                       │   │
│  │ └─▶ Returns ranked list of document IDs                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works

```python
def init_search_engine(num_products=None):
    # Select index based on product count
    if num_products == 100:
        indexes = 'indexes_100'
    elif num_products == 1000:
        indexes = 'indexes_1k'
    elif num_products == 100000:
        indexes = 'indexes_100k'
    else:
        indexes = 'indexes'
    
    # Initialize Lucene searcher with pre-built index
    search_engine = LuceneSearcher(os.path.join(BASE_DIR, f'../search_engine/{indexes}'))
    return search_engine

def get_top_n_product_from_keywords(keywords, search_engine, ...):
    keywords = ' '.join(keywords)
    hits = search_engine.search(keywords, k=SEARCH_RETURN_N)  # k=50
    docs = [search_engine.doc(hit.docid) for hit in hits]
    top_n_asins = [json.loads(doc.raw())['id'] for doc in docs]
    return [product_item_dict[asin] for asin in top_n_asins if asin in product_item_dict]
```

### Lucene BM25 Implementation

Lucene uses the same BM25 formula as our Wikinews implementation, but with optimized data structures:

\[
\text{score}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}
\]

**Default Lucene Parameters:**
- \( k_1 = 1.2 \)
- \( b = 0.75 \)

### Lucene Index Structure

Lucene uses an inverted index with additional optimizations:

```
Lucene Index Structure:
├── segments_N           # Segment metadata
├── _0.cfe               # Compound file (multiple index files)
├── _0.cfs               # Compound file data
├── _0.si                # Segment info
├── _0_Lucene84_0.tip    # Term index (FST)
├── _0_Lucene84_0.tim    # Term dictionary
├── _0_Lucene84_0.doc    # Document frequencies
├── _0_Lucene84_0.pos    # Term positions
└── _0.fnm               # Field names/metadata
```

### Special Query Prefixes

WebShop supports special query prefixes for direct filtering:

| Prefix | Function | Example |
|--------|----------|---------|
| `<r>` | Random products | Returns 50 random items |
| `<a> attribute` | Filter by attribute | `<a> wireless bluetooth` |
| `<c> category` | Filter by category | `<c> Electronics` |
| `<q> query` | Exact query match | `<q> running shoes` |

### Time Complexity

Lucene achieves near-optimal search performance through:

1. **Skip lists** for posting list traversal: \( O(\log n) \)
2. **FST (Finite State Transducer)** for term lookup: \( O(m) \) where \( m \) = term length
3. **Block-based compression** for reduced I/O

**Overall Search Complexity:** \( O(|Q| \cdot \log N + k) \)

Where:
- \( |Q| \) = number of query terms
- \( N \) = number of documents
- \( k \) = number of results requested

---

## Algorithm Comparison

### Scoring Example

For query "climate summit" on a hypothetical document:

#### Wikipedia (Substring)
```
Title: "2024 Climate Summit in Paris"
Match: "climate summit" in "2024 climate summit in paris" → TRUE
Score: 1 (binary)
```

#### Wikinews (BM25)
```
Document:
  - Title: "World leaders gather for Climate Summit" (length: 6)
  - Content: "The annual climate summit brought together..." (length: 150)
  - Category: "Politics, Environment" (length: 2)

Term: "climat" (stemmed)
  IDF = ln((26797 - 500 + 0.5) / (500 + 0.5) + 1) = 3.98
  
  Title TF = 1, field_len = 6, avg_len = 5.2
  BM25_title = 3.98 × (1 × 2.5) / (1 + 1.5 × (1 - 0.75 + 0.75 × 6/5.2))
             = 3.98 × 2.5 / 2.23 = 4.46
  Field boost: 4.46 × 10.0 = 44.6

  Content TF = 5, field_len = 150, avg_len = 200
  BM25_content = 3.98 × (5 × 2.5) / (5 + 1.5 × (1 - 0.75 + 0.75 × 150/200))
               = 3.98 × 12.5 / 6.06 = 8.21
  Field boost: 8.21 × 1.0 = 8.21

Term: "summit" (stemmed)
  Similar calculation...

Final Score: Σ(field scores) × coverage_boost
```

#### WebShop (Lucene)
```
Query: "climate summit"
Lucene BM25 score calculated internally
Returns ranked product ASINs with relevance scores
```

### Feature Matrix

| Feature | Wikipedia | Wikinews | WebShop |
|---------|-----------|----------|---------|
| Index Type | None | In-memory inverted | Disk-based Lucene |
| Ranking | None | BM25 + field boost | BM25 |
| Stemming | No | Yes (Porter-lite) | Yes (Lucene) |
| Stop Words | No | Yes | Yes |
| Field Weighting | N/A | Yes (3 fields) | Configurable |
| Phrase Matching | Substring only | Exact + word | Full |
| Fuzzy Matching | No | Stemming only | Optional |
| Result Caching | No | LRU cache | Lucene cache |
| Persistence | N/A | Pickle | Lucene files |

---

## Performance Considerations

### Memory Usage

| Component | Wikipedia | Wikinews | WebShop |
|-----------|-----------|----------|---------|
| Article Index | ~50 MB | ~100 MB | ~200 MB |
| Search Index | 0 | ~150 MB | ~500 MB (disk) |
| Cache | 0 | ~10 MB | Managed by Lucene |

### Indexing Time

| Dataset Size | Wikipedia | Wikinews | WebShop |
|--------------|-----------|----------|---------|
| 1,000 docs | N/A | ~2 sec | Pre-built |
| 10,000 docs | N/A | ~20 sec | Pre-built |
| 100,000 docs | N/A | ~3 min | Pre-built |

### Query Latency (approximate)

| Query Type | Wikipedia | Wikinews | WebShop |
|------------|-----------|----------|---------|
| Single term | 50-100 ms | 1-5 ms | 10-50 ms |
| Multi-term | 50-100 ms | 5-20 ms | 20-100 ms |
| Cached | N/A | <1 ms | <10 ms |

---

## Appendix: Configuration Parameters

### Wikinews BM25 Parameters

```python
class NewsSearchEngine:
    K1 = 1.5      # Term frequency saturation
    B = 0.75      # Length normalization
    
    FIELD_WEIGHTS = {
        'title': 10.0,
        'category': 5.0,
        'content': 1.0
    }
    
    STOP_WORDS = frozenset([
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', ...
    ])
```

### WebShop Lucene Parameters

```python
SEARCH_RETURN_N = 50    # Maximum results per query
PRODUCT_WINDOW = 10     # Products per page (default)

# Theme-specific page sizes
# webshop2025: 9 per page
# webshop2015: 12 per page
```

---

## References

1. Robertson, S., & Zaragoza, H. (2009). The Probabilistic Relevance Framework: BM25 and Beyond. *Foundations and Trends in Information Retrieval*.

2. Apache Lucene Documentation: https://lucene.apache.org/core/

3. Pyserini: https://github.com/castorini/pyserini

4. Porter, M. F. (1980). An algorithm for suffix stripping. *Program*.

