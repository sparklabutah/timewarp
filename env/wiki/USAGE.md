# Wikipedia Theme Viewer - Usage Guide

## Starting the Application

### Single Theme Mode
Run a single theme on an automatically selected free port:

```bash
./start_wiki.sh [-1|-2|-3|-4|-5|-6]
```

Options:
- `-1` : Wikipedia 2001 (Ultra-Retro) - Period-appropriate HTML 4.01, minimal CSS
- `-2` : Wikipedia 2002 (Retro) - Phase II layout with sidebar
- `-3` : Wikipedia 2003-2004 - Early MonoBook/MediaWiki style
- `-4` : Wikipedia 2005-2022 (Vector) - Classic Vector skin
- `-5` : Wikipedia 2023-2025 (Modern) - Contemporary Wikipedia design
- `-6` : Wikipedia Minimal (default) - Clean, minimal theme

The app will automatically find and use a free port starting from 5000.

### All Themes Mode
Run all themes simultaneously on consecutive free ports:

```bash
./start_wiki.sh -all
```

This will:
1. Index the Wikipedia dump once (shared across all servers)
2. Start 6 separate servers, one for each theme (1-6)
3. Automatically find free ports starting from an available base port
4. Display URLs for each running server

Example output:
```
============================================================
Starting multiple Simple Wikipedia UI servers...
Server 1 running at http://localhost:5000 (PID 12345)
Server 2 running at http://localhost:5001 (PID 12346)
Server 3 running at http://localhost:5002 (PID 12347)
Server 4 running at http://localhost:5003 (PID 12348)
Server 5 running at http://localhost:5004 (PID 12349)
Server 6 running at http://localhost:5005 (PID 12350)
============================================================
```

### Advanced Options

You can also run the Python app directly with custom port:

```bash
python3 wiki_app.py -1 --port=8080
```

Or run all themes starting from a specific port:

```bash
python3 wiki_app.py -all --port=8000
```

## Theme Authenticity

Each theme has been updated to use period-appropriate HTML and CSS:

### 1-2001 (UseModWiki Era)
- HTML 4.01 Transitional
- No CSS classes, inline elements only (`<b>`, `<em>`, `<blockquote>`)
- Basic Times New Roman font
- Simple horizontal rules and basic styling

### 2-2002 (Phase II)
- HTML 4.01 with table-based layout
- Absolutely positioned sidebar (quickbar)
- Period-appropriate CSS without modern features
- Classic blue link colors

### 3-2003-4 (Early MonoBook)
- XHTML 1.0 Transitional
- Float-based layout
- Early MediaWiki styling
- No responsive design (authentic to era)

### 4-2005-2022 (Vector)
- HTML5
- Classic Vector skin layout
- CSS with vendor prefixes for gradients
- Sidebar panel with collapsible sections

### 5-2023-2025 (Modern)
- Modern HTML5 semantic elements
- CSS Variables, Flexbox, CSS Grid
- Responsive design
- Modern interaction patterns

### 6-minimal
- Clean, minimalist design
- Lightweight and fast
- No period restrictions

## Port Selection

The app automatically finds free ports:
- Starts checking from port 5000
- Tries up to 100 consecutive ports
- Ensures no conflicts with existing services
- In `-all` mode, uses consecutive ports for each theme

## Stopping Servers

To stop the server(s):
- Press `Ctrl+C` in the terminal where it's running
- In `-all` mode, `Ctrl+C` will stop the parent process (child processes may need manual cleanup)

## First Run

On first run, the app will:
1. Parse the Wikipedia XML dump
2. Convert all wikitext to HTML
3. Cache the processed data
4. This can take 1-2 hours for the full dump

Subsequent runs will load instantly from the cache.

