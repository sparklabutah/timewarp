"""
Observation Extractor for extracting HTML and Accessibility Tree from Playwright traces.
Supports three modes: html, axtree, both
"""
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from html import escape
import re


class ObservationExtractor:
    """Extract observations (HTML, AXTree, or both) from trace data."""
    
    def __init__(self, mode: str = 'html'):
        """
        Initialize extractor with mode.
        
        Args:
            mode: One of 'html', 'axtree', or 'both'
        """
        if mode not in ['html', 'axtree', 'both']:
            raise ValueError(f"Mode must be 'html', 'axtree', or 'both', got '{mode}'")
        
        self.mode = mode
    
    def extract(self, html_content: str) -> str:
        """
        Extract observation based on mode.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Formatted observation string
        """
        if not html_content:
            return ""
        
        if self.mode == 'html':
            return self._extract_html(html_content)
        elif self.mode == 'axtree':
            return self._extract_axtree(html_content)
        else:  # both
            html = self._extract_html(html_content)
            axtree = self._extract_axtree(html_content)
            return f"=== HTML ===\n{html}\n\n=== Accessibility Tree ===\n{axtree}"
    
    def _extract_html(self, html_content: str) -> str:
        """
        Extract and clean HTML content.
        
        Args:
            html_content: Raw HTML
            
        Returns:
            Cleaned HTML string
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style tags
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            
            # Get prettified HTML
            prettified = soup.prettify()
            
            # If we need to truncate, do it at a safe boundary (not mid-tag)
            # For now, return full HTML (can add truncation later if needed)
            return prettified
            
        except Exception as e:
            # Fallback to raw HTML (no truncation)
            return html_content
    
    def _extract_axtree(self, html_content: str) -> str:
        """
        Build accessibility tree from HTML.
        
        Args:
            html_content: Raw HTML
            
        Returns:
            Accessibility tree representation
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Build accessibility tree
            axtree_lines = []
            self._build_axtree_recursive(soup.body if soup.body else soup, axtree_lines, 0)
            
            return '\n'.join(axtree_lines[:500])  # Limit to 500 lines
            
        except Exception as e:
            return f"Error building accessibility tree: {str(e)}"
    
    def _build_axtree_recursive(self, element, lines: list, depth: int):
        """
        Recursively build accessibility tree.
        
        Args:
            element: BeautifulSoup element
            lines: List to append tree lines to
            depth: Current depth in tree
        """
        if depth > 20:  # Limit depth
            return
        
        indent = "  " * depth
        
        # Get element info
        if hasattr(element, 'name') and element.name:
            tag = element.name
            
            # Build node description
            node_desc = f"{indent}[{tag}]"
            
            # Add important attributes
            if hasattr(element, 'attrs'):
                attrs = element.attrs
                
                # Add id
                if 'id' in attrs:
                    node_desc += f" id=\"{attrs['id']}\""
                
                # Add class
                if 'class' in attrs:
                    classes = ' '.join(attrs['class']) if isinstance(attrs['class'], list) else attrs['class']
                    node_desc += f" class=\"{classes}\""
                
                # Add role
                if 'role' in attrs:
                    node_desc += f" role=\"{attrs['role']}\""
                
                # Add aria-label
                if 'aria-label' in attrs:
                    node_desc += f" aria-label=\"{attrs['aria-label']}\""
                
                # Add name for inputs
                if 'name' in attrs and tag in ['input', 'button', 'select', 'textarea']:
                    node_desc += f" name=\"{attrs['name']}\""
                
                # Add type for inputs
                if 'type' in attrs and tag == 'input':
                    node_desc += f" type=\"{attrs['type']}\""
                
                # Add href for links
                if 'href' in attrs and tag == 'a':
                    href = attrs['href'][:50]  # Limit length
                    node_desc += f" href=\"{href}\""
            
            # Add text content for certain elements
            if tag in ['a', 'button', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'label', 'p', 'span']:
                text = self._get_direct_text(element)
                if text:
                    text = text[:50]  # Limit text length
                    node_desc += f" text=\"{text}\""
            
            lines.append(node_desc)
            
            # Process children
            if hasattr(element, 'children'):
                for child in element.children:
                    if hasattr(child, 'name'):
                        self._build_axtree_recursive(child, lines, depth + 1)
    
    def _get_direct_text(self, element) -> str:
        """
        Get direct text content of element (not including descendants).
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            Text content
        """
        try:
            if hasattr(element, 'strings'):
                texts = []
                for string in element.strings:
                    text = str(string).strip()
                    if text:
                        texts.append(text)
                
                result = ' '.join(texts)
                # Clean whitespace
                result = re.sub(r'\s+', ' ', result)
                return result.strip()
        except:
            pass
        
        return ""


def extract_simplified_html(html_content: str, max_length: int = 5000) -> str:
    """
    Extract simplified, text-focused HTML suitable for training.
    
    Args:
        html_content: Raw HTML
        max_length: Maximum length of output
        
    Returns:
        Simplified HTML
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unnecessary tags
        for tag in soup(['script', 'style', 'noscript', 'meta', 'link']):
            tag.decompose()
        
        # Get body or whole document
        content = soup.body if soup.body else soup
        
        # Convert to string and clean up
        text = str(content)
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text[:max_length]
        
    except Exception as e:
        return html_content[:max_length]


if __name__ == '__main__':
    # Test the extractor
    sample_html = """
    <html>
    <body>
        <h1>Test Page</h1>
        <div id="content">
            <button id="btn1" aria-label="Submit Button">Click Me</button>
            <input type="text" name="search" placeholder="Search...">
            <a href="https://example.com">Example Link</a>
        </div>
    </body>
    </html>
    """
    
    print("=== HTML Mode ===")
    extractor_html = ObservationExtractor('html')
    print(extractor_html.extract(sample_html))
    
    print("\n=== AXTree Mode ===")
    extractor_axtree = ObservationExtractor('axtree')
    print(extractor_axtree.extract(sample_html))
    
    print("\n=== Both Mode ===")
    extractor_both = ObservationExtractor('both')
    print(extractor_both.extract(sample_html)[:500])

