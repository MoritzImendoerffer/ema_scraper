"""
PDF Content Parsing (Markdown, JSON, Text extraction)

Uses pymupdf4llm with optional layout detection for semantic structure.
"""

from pathlib import Path
from typing import Optional, Union, List, Dict
import json
import logging

# Import order matters - layout must be imported before pymupdf4llm
import pymupdf.layout
import pymupdf4llm
import pymupdf

from .base import BaseParser, ParsedDocument
from .pdf_loader import load_pdf
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

@dataclass
class PdfDocument:
    json: dict = field(default_factory=dict)
    markdown: str = field(default_factory=str)
    doc_id: str = field(default_factory=str)
    doc: Optional[pymupdf.Document] = None
    error: str = field(default_factory=str)
    parsed_with: str = field(default_factory=str)

class PyMuPdfParser(BaseParser):
    """
    PDF content parser using pymupdf4llm with layout detection.
    
    Layout detection is automatically activated by importing pymupdf.layout
    before pymupdf4llm. This provides:
    - Semantic block types (heading, paragraph, table, list, code, picture)
    - Header/footer detection
    - Improved table detection
    - Reading order optimization
    
    Example:
        parser = PyMuPdfParser()
        result = parser.parse("document.pdf", doc_id="abc123")
        
        if result.is_valid:
            print(result.markdown)
            for page in result.json_data:
                for block in page.get("blocks", []):
                    print(block.get("type"), block.get("bbox"))
    """
    
    name = "pymupdf"
    
    def __init__(
        self,
        pages: Optional[List[int]] = None,
        include_header: bool = True,
        include_footer: bool = True,
    ):
        """
        Args:
            pages: List of 0-based page numbers to process. None for all pages.
            include_header: Include page headers in markdown/text output.
            include_footer: Include page footers in markdown/text output.
        """
        super().__init__(pages)
        self.include_header = include_header
        self.include_footer = include_footer
        
        # Activate layout mode
        pymupdf.layout.activate()
    
    def parse(
        self,
        source: Union[str, Path, bytes],
        doc_id: str,
        to_markdown: bool = True,
        to_json: bool = True,
        to_text: bool = False,
    ) -> ParsedDocument:
        """
        Parse a PDF document.
        
        Args:
            source: Path to PDF file or raw PDF bytes
            doc_id: Identifier for this document
            to_markdown: Extract markdown content
            to_json: Extract structured JSON (includes layout info)
            to_text: Extract plain text
            
        Returns:
            ParsedDocument with extracted content
        """
        with load_pdf(source, doc_id) as load_result:
            if not load_result.is_valid:
                return ParsedDocument(
                    doc_id=doc_id,
                    parser_name=self.name,
                    error=load_result.error
                )
            
            doc = load_result.doc
            result = ParsedDocument(
                doc_id=doc_id,
                n_pages=doc.page_count,
                parser_name=self.name,
                parser_version=f"pymupdf4llm {pymupdf4llm.VERSION}",
                source_path=load_result.source_path
            )
            
            try:
                if to_markdown:
                    result.markdown = pymupdf4llm.to_markdown(
                        doc,
                        pages=self.pages,
                        header=self.include_header,
                        footer=self.include_footer
                    )
                
                if to_json:
                    json_str = pymupdf4llm.to_json(doc, pages=self.pages)
                    result.json_data = json.loads(json_str)
                
                if to_text:
                    result.text = pymupdf4llm.to_text(
                        doc,
                        pages=self.pages,
                        header=self.include_header,
                        footer=self.include_footer
                    )
                    
            except Exception as e:
                logger.warning(f"Error parsing {doc_id}: {e}")
                result.error = f"Parse error: {e}"
        
        return result
    
    @classmethod
    def get_capabilities(cls) -> Dict[str, bool]:
        """Report PyMuPDF parser capabilities."""
        return {
            "native_text": True,
            "ocr": True,  # Via Tesseract integration
            "tables": True,
            "images": True,
            "layout_detection": True,
            "forms": True,
        }