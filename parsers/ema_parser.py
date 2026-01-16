"""
EMA Page Parser

Parses EMA web pages (main-content-wrapper) into structured JSON blocks.
Designed for BCL (Bootstrap Component Library) components used by EMA.

Usage:
    from bs4 import BeautifulSoup
    from ema_parser import EmaPageParser
    
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('main', class_='main-content-wrapper')
    
    parser = EmaPageParser()
    result = parser.parse(main)
    # result = {"blocks": [...], "links": [...]}
"""

from __future__ import annotations
from bs4 import Tag, NavigableString
from parsers.data_classes import asdict
from typing import Optional
import re
import logging
logger = logging.getLogger(__name__)

import parsers.data_classes as dc


class EmaPageParser:
    """
    Parser for EMA web pages using BCL components.
    
    Extracts structured content blocks and links from main-content-wrapper.
    """
    
    # Selectors to skip entirely
    SKIP_TAGS = {'script', 'style', 'noscript', 'svg', 'button', 'form', 'input'}
    SKIP_CLASSES = {
        'bcl-inpage-navigation', 
        'breadcrumb',
        'dropdown-menu',  # navigation dropdowns
    }
    
    # Component selectors (checked in order - more specific first)
    # Specific parsers for ema site based on https://github.com/openeuropa and https://ec.europa.eu/component-library/ec/components/
    # basically bootstrap
    COMPONENT_SELECTORS = [
        ('bcl-file', '_parse_file'),
        ('accordion', '_parse_accordion'),
        ('bcl-content-banner', '_parse_banner'),
        ('bcl-listing', '_parse_listing'),
        ('bcl-date-block', '_parse_date_block'),
        ('listing-item', '_parse_card'),  # also matches listing-item--highlight
        ('alert', '_parse_alert'),
    ]
    
    def __init__(self):
        self.links: list[dc.Link] = []
        self._processed_elements: set[int] = set()  # track by id() to avoid re-processing
    
    def parse(self, main: Tag) -> dict:
        """
        Parse main-content-wrapper and return structured content.
        
        Args:
            main: BeautifulSoup Tag for main-content-wrapper
            
        Returns:
            dict with 'blocks' (list of content blocks) and 'links' (list of links)
        """
        # reset for new page
        self.links = []
        self._processed_elements = set()
        
        blocks = self._parse_children(main)
        
        return {
            "blocks": [self._block_to_dict(b) for b in blocks],
            "links": [asdict(link) for link in self.links]
        }
    
    def _block_to_dict(self, block) -> dict:
        """Convert a block dataclass to dict, handling nested structures."""
        if isinstance(block, dict):
            return block
        
        result = asdict(block)
        
        # Handle nested content in accordions
        if isinstance(block, dc.AccordionBlock):
            result['items'] = [
                {
                    'title': item.title,
                    'content': [self._block_to_dict(b) for b in item.content]
                }
                for item in block.items
            ]
        
        # Handle nested content in blockquotes
        if isinstance(block, dc.BlockquoteBlock):
            result['content'] = [self._block_to_dict(b) for b in block.content]
        
        # Handle nested items in listings
        if isinstance(block, dc.ListingBlock):
            result['items'] = [self._block_to_dict(item) for item in block.items]
        
        return result
    
    def _should_skip(self, element: Tag) -> bool:
        """Check if element should be skipped."""
        if not isinstance(element, Tag):
            return True
        
        if element.name in self.SKIP_TAGS:
            return True
        
        if id(element) in self._processed_elements:
            return True
        
        classes = set(element.get('class', []))
        if classes & self.SKIP_CLASSES:
            return True
        
        # Skip nav elements (except when they contain actual content)
        if element.name == 'nav':
            return True
            
        return False
    
    def _mark_processed(self, element: Tag):
        """Mark element and all descendants as processed."""
        self._processed_elements.add(id(element))
        for desc in element.descendants:
            if isinstance(desc, Tag):
                self._processed_elements.add(id(desc))
    
    def _match_component(self, element: Tag) -> Optional[str]:
        """Check if element matches a known component, return parser method name."""
        classes = set(element.get('class', []))
        
        for class_name, parser_method in self.COMPONENT_SELECTORS:
            if class_name in classes:
                return parser_method
        
        return None
    
    def _parse_children(self, element: Tag) -> list:
        """
        Recursively parse children of an element.
        
        Dispatches to component parsers or recurses into containers.
        """
        blocks = []
        
        for child in element.children:
            if not isinstance(child, Tag):
                continue
                
            if self._should_skip(child):
                continue
            
            # Check for known components first
            parser_method = self._match_component(child)
            if parser_method:
                parser = getattr(self, parser_method)
                block = parser(child)
                if block:
                    blocks.append(block)
                self._mark_processed(child)
                continue
            
            # Handle standard HTML elements
            # Mark as processed is set when the element contains children that might otherwise be parsed again during recursion.
            # ['table', 'ul', 'ol', 'dl', 'blockquote']
            if child.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                block = self._parse_heading(child)
                if block:
                    blocks.append(block)
                    
            elif child.name == 'p':
                block = self._parse_paragraph(child)
                if block:
                    blocks.append(block)
                    
            elif child.name == 'table':
                block = self._parse_table(child)
                if block:
                    blocks.append(block)
                self._mark_processed(child)
                
            elif child.name in ('ul', 'ol'):
                block = self._parse_list(child)
                if block:
                    blocks.append(block)
                self._mark_processed(child)
            
            elif child.name == 'dl':
                block = self._parse_description_list(child)
                if block:
                    blocks.append(block)
                self._mark_processed(child)
            
            elif child.name == 'blockquote':
                block = self._parse_blockquote(child)
                if block:
                    blocks.append(block)
                self._mark_processed(child)
                
            elif child.name == 'a':
                # Standalone link - extract and possibly create a paragraph
                self._extract_link(child)
                
            elif child.name in ('div', 'section', 'article', 'main', 'aside', 'header', 'footer', 'span'):
                # Container element - recurse
                nested = self._parse_children(child)
                blocks.extend(nested)
                
            else:
                # Not a content element - recurse to find nested content
                logger.warning(f"Unkown case during parsing occured for {element}")
                nested = self._parse_children(child)
                blocks.extend(nested)
                        
            # Other elements (blockquote, pre, etc.) - could add more parsers
        
        return blocks
    
    def _parse_heading(self, el: Tag) -> Optional[dc.HeadingBlock]:
        """Parse h1-h6 elements."""
        text = self._get_text(el)
        if not text:
            return None
        
        level = int(el.name[1])  # h1 -> 1, h2 -> 2, etc.
        
        # Extract any links in the heading
        self._extract_links(el)
        
        return dc.HeadingBlock(level=level, text=text)
    
    def _parse_paragraph(self, el: Tag) -> Optional[dc.ParagraphBlock]:
        """Parse paragraph elements."""
        text = self._get_text(el)
        if not text:
            return None
        
        # Extract links
        self._extract_links(el)
        
        return dc.ParagraphBlock(text=text)
    
    def _parse_list(self, el: Tag) -> Optional[dc.ListBlock]:
        """Parse ul/ol lists."""
        items = []
        
        for li in el.find_all('li', recursive=True):
            text = self._get_text(li)
            if text:
                items.append(text)
                self._extract_links(li)
        
        if not items:
            return None
        
        return dc.ListBlock(
            ordered=(el.name == 'ol'),
            items=items
        )
    
    def _parse_table(self, el: Tag) -> Optional[dc.TableBlock]:
        """Parse table elements."""
        headers = []
        rows = []
        
        # Extract headers from thead or first row
        thead = el.find('thead')
        if thead:
            for th in thead.find_all('th'):
                headers.append(self._get_text(th))
                self._extract_links(th)
        
        # Extract rows from tbody or direct tr children
        tbody = el.find('tbody') or el
        for tr in tbody.find_all('tr', recursive=False):
            # Skip header row if no thead
            cells = tr.find_all(['td', 'th'])
            if not headers and all(c.name == 'th' for c in cells):
                headers = [self._get_text(c) for c in cells]
                for c in cells:
                    self._extract_links(c)
                continue
            
            row = []
            for cell in cells:
                row.append(self._get_text(cell))
                self._extract_links(cell)
            
            if row:
                rows.append(row)
        
        if not headers and not rows:
            return None
        
        return dc.TableBlock(headers=headers, rows=rows)
    
    def _parse_file(self, el: Tag) -> Optional[dc.FileBlock]:
        """
        Parse .bcl-file component.
        
        Structure:
        <div class="bcl-file" data-ema-document-type="...">
          <div class="file-title-metadata">
            <p class="file-title">...</p>
            <small class="reference-number..."><span class="value">...</span></small>
          </div>
          <div class="file-language-links">
            <p class="language-meta">English (EN) <span>(310.46 KB - PDF)</span></p>
            <small class="first-published..."><time>...</time></small>
            <small class="last-updated..."><time>...</time></small>
            <a href="...">View</a>
          </div>
        </div>
        """
        block = dc.FileBlock()
        
        # Document type from data attribute
        block.document_type = el.get('data-ema-document-type')
        
        # Title
        title_el = el.find(class_='file-title')
        if title_el:
            block.title = self._get_text(title_el)
        
        # Reference number
        ref_el = el.find(class_=lambda x: x and 'reference-number' in x)
        if ref_el:
            value = ref_el.find(class_='value')
            if value:
                block.reference_number = self._get_text(value)
        
        # Language and file info
        lang_el = el.find(class_='language-meta')
        if lang_el:
            # "English (EN) (310.46 KB - PDF)"
            lang_text = self._get_text(lang_el)
            
            # Parse language
            lang_match = re.match(r'^([^(]+(?:\([A-Z]{2}\))?)', lang_text)
            if lang_match:
                block.language = lang_match.group(1).strip()
            
            # Parse size and format
            meta_match = re.search(r'\(([^)]+)\s*-\s*([^)]+)\)', lang_text)
            if meta_match:
                block.file_size = meta_match.group(1).strip()
                block.file_format = meta_match.group(2).strip()
        
        # Dates
        first_pub = el.find(class_=lambda x: x and 'first-published' in x)
        if first_pub:
            time_el = first_pub.find('time')
            if time_el and time_el.get('datetime'):
                block.first_published = time_el['datetime'][:10]  # YYYY-MM-DD
            elif time_el:
                block.first_published = self._get_text(time_el)
        
        last_upd = el.find(class_=lambda x: x and 'last-updated' in x)
        if last_upd:
            time_el = last_upd.find('time')
            if time_el and time_el.get('datetime'):
                block.last_updated = time_el['datetime'][:10]
            elif time_el:
                block.last_updated = self._get_text(time_el)
        
        # URL (from View/Download link)
        link_el = el.find('a', href=True)
        if link_el:
            block.url = link_el['href']
            self.links.append(dc.Link(
                text=block.title or self._get_text(link_el),
                href=link_el['href']
            ))
        
        if not block.title and not block.url:
            return None
        
        return block
    
    def _parse_accordion(self, el: Tag) -> Optional[AccordionBlock]:
        """
        Parse .accordion component with nested content.
        
        Structure:
        <div class="accordion">
          <div class="accordion-item">
            <h2 class="accordion-header">
              <button>Title</button>
            </h2>
            <div class="accordion-collapse">
              <div class="accordion-body">
                ... content ...
              </div>
            </div>
          </div>
        </div>
        """
        items = []
        
        for item_el in el.find_all(class_='accordion-item', recursive=True):
            # Extract title from header/button
            header = item_el.find(class_='accordion-header')
            title = ""
            if header:
                button = header.find('button')
                title = self._get_text(button) if button else self._get_text(header)
            
            # Extract content from accordion-body
            content = []
            body = item_el.find(class_='accordion-body')
            if body:
                # Recursive parse of accordion content
                content = self._parse_children(body)
            
            if title or content:
                items.append(dc.AccordionItem(title=title, content=content))
        
        if not items:
            return None
        
        return dc.AccordionBlock(items=items)
    
    def _parse_banner(self, el: Tag) -> Optional[dc.BannerBlock]:
        """
        Parse .bcl-content-banner component.
        
        Structure:
        <div class="bcl-content-banner">
          <article class="card">
            <div class="img-wrapper"><img src="..." /></div>
            <div class="card-body">
              <h1 class="content-banner-title">Title</h1>
              <div class="content">Summary text</div>
            </div>
          </article>
        </div>
        """
        block = dc.BannerBlock()
        
        # Title
        title_el = el.find(class_='content-banner-title') or el.find('h1')
        if title_el:
            block.title = self._get_text(title_el)
            self._extract_links(title_el)
        
        # Summary
        content_el = el.find(class_='content') or el.find(class_='card-text')
        if content_el:
            block.summary = self._get_text(content_el)
            self._extract_links(content_el)
        
        # Image
        img = el.find('img')
        if img and img.get('src'):
            block.image_url = img['src']
        
        # Link
        link = el.find('a', href=True)
        if link:
            block.link_url = link['href']
            self._extract_link(link)
        
        if not block.title:
            return None
        
        return block
    
    def _parse_date_block(self, el: Tag) -> Optional[dc.DateBlock]:
        """
        Parse .bcl-date-block component (typically <time> element).
        
        Structure:
        <time class="bcl-date-block" datetime="2026-01-08">
          <span>08 Jan</span>
          <span>2026</span>
        </time>
        """
        block = dc.DateBlock()
        
        # ISO date from datetime attribute
        if el.get('datetime'):
            block.date = el['datetime']
        
        # Display text
        block.display_text = self._get_text(el)
        
        if not block.date and not block.display_text:
            return None
        
        return block
    
    def _parse_card(self, el: Tag) -> Optional[dc.CardBlock]:
        """
        Parse card/listing-item component.
        
        Structure:
        <article class="listing-item card">
          <div class="img-wrapper"><img src="..." /></div>
          <div class="card-body">
            <h4 class="card-title"><a href="...">Title</a></h4>
            <div class="card-text">Description</div>
            <div class="metadata">Date, Category</div>
          </div>
        </article>
        """
        block = dc.CardBlock()
        
        # Title (look for card-title or heading)
        title_el = el.find(class_='card-title') or el.find(class_='teaser-title')
        if title_el:
            block.title = self._get_text(title_el)
            
            # Link from title
            link = title_el.find('a', href=True)
            if link:
                block.link_url = link['href']
                self._extract_link(link)
        
        # Text/description
        text_el = el.find(class_='card-text')
        if text_el:
            block.text = self._get_text(text_el)
            self._extract_links(text_el)
        
        # Image
        img = el.find('img')
        if img and img.get('src'):
            block.image_url = img['src']
        
        # Metadata (dates, categories, etc.)
        metadata = []
        for meta_el in el.find_all(class_='metadata-item'):
            meta_text = self._get_text(meta_el)
            if meta_text:
                metadata.append(meta_text)
        if metadata:
            block.metadata = metadata
        
        if not block.title:
            return None
        
        return block
    
    def _parse_listing(self, el: Tag) -> Optional[dc.ListingBlock]:
        """
        Parse .bcl-listing component containing multiple cards.
        
        Structure:
        <div class="bcl-listing bcl-listing--highlight-3-col">
          <div class="row">
            <div class="col"><article class="listing-item">...</article></div>
            <div class="col"><article class="listing-item">...</article></div>
          </div>
        </div>
        """
        block = dc.ListingBlock()
        
        # Extract variant from class
        classes = el.get('class', [])
        for cls in classes:
            if cls.startswith('bcl-listing--'):
                block.variant = cls.replace('bcl-listing--', '')
                break
        
        # Find all listing items/cards within
        items = []
        for item_el in el.find_all(class_=lambda x: x and ('listing-item' in x or x == 'card')):
            card = self._parse_card(item_el)
            if card:
                items.append(card)
                self._mark_processed(item_el)
        
        if not items:
            return None
        
        block.items = items
        return block
    
    def _parse_alert(self, el: Tag) -> Optional[dc.AlertBlock]:
        """
        Parse .alert component (notifications).
        
        Structure:
        <div class="alert alert-info" role="alert">
          <div class="notification--content">
            <p>Message text</p>
          </div>
        </div>
        """
        block = dc.AlertBlock()
        
        # Extract variant from class (alert-info, alert-warning, etc.)
        classes = el.get('class', [])
        for cls in classes:
            if cls.startswith('alert-') and cls != 'alert-dismissible':
                block.variant = cls.replace('alert-', '')
                break
        
        # Message content
        content_el = el.find(class_='notification--content') or el
        block.message = self._get_text(content_el)
        self._extract_links(content_el)
        
        if not block.message:
            return None
        
        return block
    
    def _parse_description_list(self, el: Tag) -> Optional[dc.DescriptionListBlock]:
        """
        Parse <dl> description list elements.
        
        Structure:
        <dl>
          <dt>Term 1</dt>
          <dd>Description 1</dd>
          <dt>Term 2</dt>
          <dd>Description 2</dd>
        </dl>
        
        Output: list of [term, description] pairs
        """
        items = []
        current_term = None
        
        for child in el.children:
            if not isinstance(child, Tag):
                continue
            
            if child.name == 'dt':
                current_term = self._get_text(child)
                self._extract_links(child)
            elif child.name == 'dd':
                description = self._get_text(child)
                self._extract_links(child)
                
                # Pair with current term, or use empty string if no term
                term = current_term if current_term is not None else ""
                items.append([term, description])
                current_term = None
        
        # Handle trailing term without description
        if current_term is not None:
            items.append([current_term, ""])
        
        if not items:
            return None
        
        return dc.DescriptionListBlock(items=items)
    
    def _parse_blockquote(self, el: Tag) -> Optional[dc.BlockquoteBlock]:
        """
        Parse <blockquote> elements with nested content.
        """
        content = self._parse_children(el)
        
        # If no nested blocks, try to get text directly
        if not content:
            text = self._get_text(el)
            if text:
                content = [dc.ParagraphBlock(text=text)]
        
        if not content:
            return None
        
        return dc.BlockquoteBlock(content=content)
    
    
    def _get_text(self, el: Tag) -> str:
        """Extract clean text from element."""
        if el is None:
            return ""
        text = el.get_text(separator=' ', strip=True)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _extract_links(self, el: Tag):
        """Extract all links from element and add to self.links."""
        for a in el.find_all('a', href=True):
            self._extract_link(a)
    
    def _extract_link(self, a: Tag):
        """Extract a single link."""
        href = a.get('href', '')
        if not href or href.startswith('#') or href.startswith('javascript:'):
            return
        
        text = self._get_text(a)
        if not text:
            text = href
        
        self.links.append(dc.Link(text=text, href=href))
        
        
class MarkdownConverter:
    """
    Converts parsed EMA page blocks to markdown.
    
    Usage:
        result = parser.parse(main)
        converter = MarkdownConverter()
        markdown = converter.convert(result['blocks'])
    """
    
    # Block types to skip (navigational/noise)
    SKIP_TYPES = {'banner', 'listing', 'card', 'alert', 'date'}
    
    def __init__(self, skip_types: set[str] = None):
        """
        Args:
            skip_types: Block types to skip. Defaults to SKIP_TYPES.
        """
        self.skip_types = skip_types if skip_types is not None else self.SKIP_TYPES
    
    def convert(self, blocks: list[dict]) -> str:
        """
        Convert list of blocks to markdown string.
        
        Args:
            blocks: List of block dicts from EmaPageParser
            
        Returns:
            Markdown string
        """
        parts = []
        
        for block in blocks:
            block_type = block.get('type')
            
            if block_type in self.skip_types:
                continue
            
            renderer = getattr(self, f'_render_{block_type}', None)
            if renderer:
                rendered = renderer(block)
                if rendered:
                    parts.append(rendered)
        
        return '\n\n'.join(parts)
    
    def _render_heading(self, block: dict) -> str:
        level = block.get('level', 1)
        text = block.get('text', '')
        return f"{'#' * level} {text}"
    
    def _render_paragraph(self, block: dict) -> str:
        return block.get('text', '')
    
    def _render_list(self, block: dict) -> str:
        items = block.get('items', [])
        ordered = block.get('ordered', False)
        
        lines = []
        for i, item in enumerate(items, 1):
            prefix = f"{i}." if ordered else "-"
            lines.append(f"{prefix} {item}")
        
        return '\n'.join(lines)
    
    def _render_description_list(self, block: dict) -> str:
        items = block.get('items', [])
        
        lines = []
        for term, description in items:
            if term and description:
                lines.append(f"**{term}:** {description}")
            elif term:
                lines.append(f"**{term}**")
            elif description:
                lines.append(description)
        
        return '\n'.join(lines)
    
    def _render_table(self, block: dict) -> str:
        headers = block.get('headers', [])
        rows = block.get('rows', [])
        
        if not headers and not rows:
            return ''
        
        lines = []
        
        # Header row
        if headers:
            lines.append('| ' + ' | '.join(headers) + ' |')
            lines.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        
        # Data rows
        for row in rows:
            # Ensure row has same number of columns as header
            if headers:
                while len(row) < len(headers):
                    row.append('')
            lines.append('| ' + ' | '.join(str(cell) for cell in row) + ' |')
        
        return '\n'.join(lines)
    
    def _render_blockquote(self, block: dict) -> str:
        content = block.get('content', [])
        
        # Recursively render nested content
        inner_md = self.convert(content)
        
        # Prefix each line with >
        lines = inner_md.split('\n')
        return '\n'.join(f"> {line}" for line in lines)
    
    def _render_file(self, block: dict) -> str:
        title = block.get('title', 'Untitled')
        url = block.get('url', '')
        
        # Title with link
        if url:
            line1 = f"**[{title}]({url})**"
        else:
            line1 = f"**{title}**"
        
        # Metadata line
        meta_parts = []
        
        if block.get('reference_number'):
            meta_parts.append(f"Reference: {block['reference_number']}")
        
        file_info = []
        if block.get('file_format'):
            file_info.append(block['file_format'])
        if block.get('file_size'):
            file_info.append(block['file_size'])
        if file_info:
            meta_parts.append(', '.join(file_info))
        
        if block.get('first_published'):
            meta_parts.append(f"Published: {block['first_published']}")
        
        if meta_parts:
            line2 = ' | '.join(meta_parts)
            return f"{line1}  \n{line2}"
        
        return line1
    
    def _render_accordion(self, block: dict) -> str:
        items = block.get('items', [])
        
        parts = []
        for item in items:
            title = item.get('title', '')
            content = item.get('content', [])
            
            # Render title as h3
            if title:
                parts.append(f"### {title}")
            
            # Render nested content
            if content:
                inner_md = self.convert(content)
                if inner_md:
                    parts.append(inner_md)
        
        return '\n\n'.join(parts)




def parse_ema_page(html: str) -> dict:
    """
    Convenience function to parse EMA HTML page.
    
    Args:
        html: Raw HTML string
        
    Returns:
        dict with 'blocks' and 'links', or empty dict if main content not found
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'html.parser')
    main = soup.find('main', class_='main-content-wrapper')
    
    if not main:
        return {"blocks": [], "links": []}
    
    parser = EmaPageParser()
    return parser.parse(main)

def ema_to_markdown(html: str, skip_types: set[str] = None) -> str:
    """
    Convenience function to convert EMA HTML page directly to markdown.
    
    Args:
        html: Raw HTML string
        skip_types: Block types to skip (default: banner, listing, card, alert, date)
        
    Returns:
        Markdown string
    """
    result = parse_ema_page(html)
    converter = MarkdownConverter(skip_types=skip_types)
    return converter.convert(result['blocks'])

if __name__ == '__main__':
    import json
    import sys
    
    sample_html = """
    <main class="main-content-wrapper">
        <h1>Test Page</h1>
        <p>This is a <a href="/link1">test link</a> paragraph.</p>
        <h2>Section</h2>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        <div class="bcl-file" data-ema-document-type="guideline">
            <div class="file-title-metadata">
                <p class="file-title">Test Document</p>
            </div>
            <div class="file-language-links">
                <p class="language-meta">English (EN) (1.2 MB - PDF)</p>
                <a href="/docs/test.pdf">View</a>
            </div>
        </div>
    </main>
    """
    
    result = parse_ema_page(sample_html)
    print(json.dumps(result, indent=2))