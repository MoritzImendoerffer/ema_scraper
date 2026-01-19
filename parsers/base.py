"""
Base classes for PDF parsing.

Defines the common interface that all parser implementations must follow.
This allows swapping parsers based on document type or cluster analysis.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Union, List, Dict
from pathlib import Path


@dataclass
class ParsedDocument:
    """
    Common output format for all parsers.
    
    All parser implementations must return this structure,
    enabling consistent downstream processing regardless of
    which parser was used.
    """
    doc_id: str
    markdown: str = ""
    json_data: Optional[list] = None  # List of page dicts from pymupdf4llm
    text: str = ""
    n_pages: int = 0
    parser_name: str = ""
    parser_version: str = ""
    error: Optional[str] = None
    source_path: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        return self.error is None
    
    def has_content(self) -> bool:
        """Check if any content was extracted."""
        return bool(self.markdown or self.text or self.json_data)


class BaseParser(ABC):
    """
    Abstract base class for PDF parsers.
    
    Subclasses must implement:
        - parse(): Extract content from a single document
        - get_capabilities(): Report what the parser can do
    
    Example implementation:
        class MyParser(BaseParser):
            name = "myparser"
            
            def parse(self, source, doc_id, **kwargs) -> ParsedDocument:
                # ... extraction logic ...
                return ParsedDocument(
                    doc_id=doc_id,
                    markdown=extracted_md,
                    parser_name=self.name
                )
            
            @classmethod
            def get_capabilities(cls) -> dict:
                return {"native_text": True, "ocr": False, ...}
    """
    
    name: str = "base"  # Override in subclasses
    
    def __init__(self, pages: Optional[List[int]] = None):
        """
        Args:
            pages: List of 0-based page numbers to process. None for all.
        """
        self.pages = pages
    
    @abstractmethod
    def parse(
        self,
        source: Union[str, Path, bytes],
        doc_id: str,
        **kwargs
    ) -> ParsedDocument:
        """
        Parse a PDF document.
        
        Args:
            source: Path to PDF file or raw PDF bytes
            doc_id: Document identifier (URL, MongoDB _id, etc.)
            **kwargs: Parser-specific options
            
        Returns:
            ParsedDocument with extracted content
        """
        pass
    
    def parse_batch(
        self,
        sources: List[Union[str, Path, bytes]],
        doc_ids: List[str],
        **kwargs
    ) -> List[ParsedDocument]:
        """
        Parse multiple documents.
        
        Args:
            sources: List of paths or bytes
            doc_ids: List of identifiers (same order as sources)
            **kwargs: Arguments passed to parse()
            
        Returns:
            List of ParsedDocument objects
        """
        if len(sources) != len(doc_ids):
            raise ValueError("sources and doc_ids must have same length")
        return [self.parse(s, d, **kwargs) for s, d in zip(sources, doc_ids)]
    
    @classmethod
    def get_capabilities(cls) -> Dict[str, bool]:
        """
        Report parser capabilities.
        
        Used by ParserRouter to select appropriate parser
        for different document types.
        
        Returns:
            Dict with capability flags
        """
        return {
            "native_text": False,  # Extract text from native PDFs
            "ocr": False,          # OCR scanned documents
            "tables": False,       # Structured table extraction
            "images": False,       # Image extraction
            "layout_detection": False,  # Semantic layout analysis
            "forms": False,        # PDF form field extraction
        }


class ParserRouter:
    """
    Route documents to appropriate parsers.
    
    Supports:
        - Default parser selection
        - Cluster-based parser assignment
        - Capability-based selection (future)
    
    Example:
        router = ParserRouter(default_parser=PyMuPdfParser())
        
        # Assign parser to problematic cluster
        router.set_cluster_parser(cluster_id=3, parser=AlternativeParser())
        
        # Parse with automatic routing
        result = router.parse(source, doc_id, cluster_id=3)
    """
    
    def __init__(self, default_parser: Optional[BaseParser] = None):
        """
        Args:
            default_parser: Parser to use when no specific routing applies
        """
        self.default_parser = default_parser
        self.cluster_parsers: Dict[int, BaseParser] = {}
    
    def set_default_parser(self, parser: BaseParser):
        """Set the default parser."""
        self.default_parser = parser
    
    def set_cluster_parser(self, cluster_id: int, parser: BaseParser):
        """Assign a specific parser to a cluster."""
        self.cluster_parsers[cluster_id] = parser
    
    def get_parser(self, cluster_id: Optional[int] = None) -> BaseParser:
        """
        Get the appropriate parser for a cluster.
        
        Args:
            cluster_id: Cluster ID from clustering analysis
            
        Returns:
            Parser instance
            
        Raises:
            ValueError: If no parser available
        """
        if cluster_id is not None and cluster_id in self.cluster_parsers:
            return self.cluster_parsers[cluster_id]
        
        if self.default_parser is not None:
            return self.default_parser
        
        raise ValueError("No parser available. Set a default parser or cluster mapping.")
    
    def parse(
        self,
        source: Union[str, Path, bytes],
        doc_id: str,
        cluster_id: Optional[int] = None,
        **kwargs
    ) -> ParsedDocument:
        """
        Parse document using appropriate parser.
        
        Args:
            source: Path to PDF or raw bytes
            doc_id: Document identifier
            cluster_id: Optional cluster ID for routing
            **kwargs: Passed to parser
            
        Returns:
            ParsedDocument from selected parser
        """
        parser = self.get_parser(cluster_id)
        return parser.parse(source, doc_id, **kwargs)
    
    def list_cluster_assignments(self) -> Dict[int, str]:
        """Return mapping of cluster IDs to parser names."""
        return {
            cid: parser.name 
            for cid, parser in self.cluster_parsers.items()
        }