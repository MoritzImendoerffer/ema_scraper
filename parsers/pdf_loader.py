"""
PDF Loading utilities.

Simple loader that validates and opens PDFs.
Caller is responsible for closing the document.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import logging
import os

import pymupdf

logger = logging.getLogger(__name__)

os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/5/tessdata/"

PDF_MAGIC = b'%PDF-'


@dataclass
class LoadResult:
    """
    Result of PDF loading attempt.
    
    Can be used as context manager for automatic cleanup:
        with load_pdf("doc.pdf", "id") as result:
            if result.is_valid:
                # work with result.doc
    
    Or manually:
        result = load_pdf("doc.pdf", "id")
        try:
            # work with result.doc
        finally:
            result.close()
    """
    doc: Optional[pymupdf.Document] = None
    doc_id: str = ""
    source_path: Optional[str] = None
    error: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        return self.doc is not None and self.error is None
    
    def close(self):
        """Close the document if open."""
        if self.doc is not None:
            try:
                self.doc.close()
            except Exception as e:
                logger.warning(f"Error closing document {self.doc_id}: {e}")
            self.doc = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


def load_pdf(source: Union[str, Path, bytes], doc_id: str) -> LoadResult:
    """
    Load and validate a PDF.
    
    Args:
        source: Path to PDF file or raw PDF bytes
        doc_id: Identifier for this document
        
    Returns:
        LoadResult with open document or error.
        Caller must call result.close() when done.
    
    Example:
        result = load_pdf("document.pdf", "doc123")
        if result.is_valid:
            print(f"Pages: {result.doc.page_count}")
            # ... do work ...
            result.close()
        else:
            print(f"Error: {result.error}")
    """
    # Get bytes
    if isinstance(source, bytes):
        pdf_bytes = source
        source_path = None
    else:
        source_path = str(source)
        try:
            with open(source, 'rb') as f:
                pdf_bytes = f.read()
        except Exception as e:
            logger.warning(f"Failed to read {source_path}: {e}")
            return LoadResult(
                doc_id=doc_id,
                source_path=source_path,
                error=f"Failed to read file: {e}"
            )
    
    # Validate magic bytes
    if len(pdf_bytes) < 5 or pdf_bytes[:5] != PDF_MAGIC:
        return LoadResult(
            doc_id=doc_id,
            source_path=source_path,
            error="Invalid PDF (bad magic bytes)"
        )
    
    # Open
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        return LoadResult(
            doc=doc,
            doc_id=doc_id,
            source_path=source_path
        )
    except Exception as e:
        logger.warning(f"Failed to open PDF {doc_id}: {e}")
        return LoadResult(
            doc_id=doc_id,
            source_path=source_path,
            error=f"Failed to open PDF: {e}"
        )