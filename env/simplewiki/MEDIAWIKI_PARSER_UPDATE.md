# MediaWiki Parser Integration

## What Changed

The Simple Wikipedia UI now uses **mwparserfromhell**, a proper MediaWiki parser library, instead of the custom regex-based parser.

## Installation

Install the new dependency:

```bash
pip install -r requirements.txt
```

Or directly:

```bash
pip install mwparserfromhell==0.6.6
```

## Benefits of MediaWiki Parser

### Previous (Custom Regex Parser):

- ❌ Limited template handling (simple regex removal)
- ❌ No proper nesting support
- ❌ Failed on complex wikitext structures
- ❌ Manual regex patterns for everything

### Now (mwparserfromhell):

- ✅ **Proper template parsing** - correctly handles nested templates
- ✅ **Robust comment removal** - safely removes HTML comments
- ✅ **Tag filtering** - removes `<ref>`, `<gallery>`, and other MediaWiki tags
- ✅ **Better wikitext understanding** - uses MediaWiki's own parsing logic
- ✅ **More accurate** - handles edge cases and complex markup

## How It Works

1. **Parse Phase**: `mwparserfromhell.parse()` creates a parse tree of the wikitext
2. **Clean Phase**: Removes templates, comments, and tags using the parser's filter methods
3. **Extract Phase**: Gets cleaned wikitext as a string
4. **Convert Phase**: Existing regex converter transforms to HTML (headings, links, lists, etc.)

## What's Still Using Regex

The final HTML conversion still uses regex patterns for:

- Headings: `==Title==` → `<h2>Title</h2>`
- Bold/Italic: `'''bold'''` → `<strong>bold</strong>`
- Internal links: `[[Article]]` → `<a href="/wiki/Article">Article</a>`
- Lists: `*` and `#` → `<ul>/<ol>`

This is intentional - the parser handles the complex MediaWiki syntax, then simple regex converts the cleaned markup to HTML.

## Re-indexing Required

After installing the new parser, you need to **rebuild the article index**:

```bash
# Delete the old index
rm wiki_index.pkl

# Restart the app - it will auto-regenerate with the new parser
python wiki_app.py -3  # or your preferred theme
```

The initial indexing will take the same amount of time, but articles will be parsed more accurately!

## Testing

You can test with a few articles first:

1. Edit `wiki_app.py` line 43: Set `MAX_ARTICLES = 1000`
2. Delete `wiki_index.pkl`
3. Run the app
4. Check if complex articles with templates render correctly

Once satisfied, set `MAX_ARTICLES = None` for full indexing.

## Troubleshooting

If you get import errors:

```bash
pip install --upgrade mwparserfromhell
```

If parsing seems slower:

- The parser is slightly slower than pure regex, but more accurate
- Pre-caching during indexing means serving is still instant
- Consider keeping `MAX_ARTICLES` limit for testing environments
