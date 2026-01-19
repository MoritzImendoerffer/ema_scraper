"""
PDF Parsing and Document Analysis Package

Modules:
- base: Abstract base classes for parsers
- pdf_loader: Safe PDF loading with context management
- pdf_parser: Content extraction (markdown, JSON, text) via pymupdf4llm
- document_profile: Feature extraction from parsed JSON
- cluster_analysis: Clustering and analysis framework

Example:
    from parsers import PyMuPdfParser, DocumentProfileExtractor, DocumentClusterAnalyzer
    
    # Parse PDFs
    parser = PyMuPdfParser()
    doc = parser.parse("document.pdf", doc_id="abc123")
    
    # Extract features
    extractor = DocumentProfileExtractor()
    profile = extractor.extract(doc.json_data, doc_id="abc123")
    
    # Cluster documents
    analyzer = DocumentClusterAnalyzer(dim_reduction="umap", clustering="hdbscan")
    results = analyzer.fit(profiles)
"""

from .base import BaseParser, ParsedDocument, ParserRouter
from .pdf_loader import LoadResult, load_pdf
from .pdf_parser import PyMuPdfParser

__all__ = [
    # Base classes
    "BaseParser",
    "ParsedDocument",
    "ParserRouter",
    
    # Loader
    "LoadResult", 
    "load_pdf",
    
    # Parser implementations
    "PyMuPdfParser",
    
    # Profile
    
    # Clustering
    
]