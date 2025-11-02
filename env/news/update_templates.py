#!/usr/bin/env python3
"""
Script to update all template files to use the new article_url filter
This handles external HTTP/HTTPS links properly
"""

import os
import re
from pathlib import Path

# Base directory containing themes
THEMES_DIR = Path(__file__).parent / 'themes'

def update_template(file_path):
    """Update a single template file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # Pattern 1: href="/news/{{ variable }}" or href="/news/{{ variable.property }}"
    # Replace with: href="{{ variable|article_url }}" with conditional target
    patterns = [
        # Simple variable patterns
        (r'<a\s+href="/news/\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*?)\s*\}\}"',
         r'<a {% if \1|is_external_link %}target="_blank" rel="noopener noreferrer"{% endif %} href="{{ \1|article_url }}"'),
        
        # With filters or slices
        (r'<a\s+href="/news/\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*?)(\[[^\]]+\]|\|[^\}]+)?\s*\}\}"',
         r'<a {% if \1|is_external_link %}target="_blank" rel="noopener noreferrer"{% endif %} href="{{ \1|article_url }}"'),
    ]
    
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            if content != original_content:
                changes.append(f"Updated pattern: {pattern[:50]}...")
                original_content = content
    
    # Special handling for JavaScript template literals in 404.html
    # /news/${encodeURIComponent(result.title)} should become result.title directly or with proper check
    js_pattern = r'/news/\$\{encodeURIComponent\(([^)]+)\)\}'
    if re.search(js_pattern, content):
        # For JavaScript, we need a different approach - check if it's external
        content = re.sub(
            js_pattern,
            r'${(\1.startsWith("http://") || \1.startsWith("https://")) ? \1 : `/news/${encodeURIComponent(\1)}`}',
            content
        )
        changes.append("Updated JavaScript template literal")
    
    # Only write if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, changes
    
    return False, []

def main():
    """Update all template files"""
    updated_files = []
    
    # Find all HTML files in themes directory
    for html_file in THEMES_DIR.rglob('*.html'):
        was_updated, changes = update_template(html_file)
        if was_updated:
            updated_files.append(str(html_file.relative_to(THEMES_DIR)))
            print(f"✓ Updated: {html_file.relative_to(THEMES_DIR)}")
            for change in changes:
                print(f"  - {change}")
    
    print(f"\n{'='*60}")
    print(f"Total files updated: {len(updated_files)}")
    if updated_files:
        print("\nUpdated files:")
        for f in updated_files:
            print(f"  - {f}")

if __name__ == '__main__':
    main()
