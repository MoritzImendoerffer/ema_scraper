"""
Document Style Extraction for PDF Classification

Extracts font/style features from PDFs to enable unsupervised clustering
of document types. Produces tokenized representations suitable for 
sklearn's CountVectorizer and clustering algorithms like DBSCAN.
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
import os
import fitz
from typing import Optional

os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/5/tessdata/"

@dataclass
class StyleProfile:
    """
    Style fingerprint of a PDF document.
    
    Attributes:
        doc_id: MongoDB _id or other identifier linking to parent document
        source_path: File path processed (for debugging/reprocessing)
        style_counts: Histogram of decomposed style tokens {"sz_12.0": 45, ...}
        style_sequence: Ordered list of composite style identifiers per span
        tokens: Flattened decomposed tokens for CountVectorizer
        n_pages: Number of pages processed
        is_empty: True if no extractable styles found
        error: Optional error message for debugging
    """
    doc_id: str
    source_path: str
    style_counts: dict = field(default_factory=dict)
    style_sequence: list = field(default_factory=list)
    tokens: list = field(default_factory=list)
    n_pages: int = 0
    is_empty: bool = True
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dict for MongoDB storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StyleProfile":
        """Deserialize from MongoDB document."""
        return cls(**data)


class DocumentStyleExtractor:
    """
    Extracts style features from PDF documents.
    
    Produces decomposed tokens (sz_12.0, font_Arial, flag_bold) for flexible
    vectorization, plus composite sequences for structural pattern analysis.
    
    Example:
        extractor = DocumentStyleExtractor(n_pages=10)
        profile = extractor.extract("document.pdf", doc_id="abc123")
        
        # For sklearn pipeline:
        vectorizer = CountVectorizer(tokenizer=lambda x: x, lowercase=False)
        X = vectorizer.fit_transform([profile.tokens])
    """

    def __init__(self, n_pages: Optional[int] = None):
        """
        Args:
            n_pages: Number of pages to process. None for all pages.
        """
        self.n_pages = n_pages

    def extract(self, source: str | Path | bytes, doc_id: str) -> StyleProfile:
        """
        Extract style profile from a PDF file or bytes.
        
        Args:
            source: Path to PDF file (str or Path) or raw PDF bytes
            doc_id: Identifier to link back to MongoDB document
            
        Returns:
            StyleProfile with extracted features, or empty profile on error
        """
        # Determine input type and get bytes
        if isinstance(source, bytes):
            pdf_bytes = source
            source_path = None
        else:
            source_path = str(source)
            try:
                with open(source, 'rb') as f:
                    pdf_bytes = f.read()
            except Exception as e:
                return StyleProfile(
                    doc_id=doc_id,
                    source_path=source_path,
                    error=f"Failed to read file: {e}"
                )

        # Validate PDF magic bytes
        if not self._is_valid_pdf(pdf_bytes):
            return StyleProfile(
                doc_id=doc_id,
                source_path=source_path,
                error="Not a valid PDF file"
            )

        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            return StyleProfile(
                doc_id=doc_id,
                source_path=source_path,
                error=f"Failed to open PDF: {str(e)}"
            )

        try:
            style_counts, style_sequence, tokens, n_pages = self._extract_styles(doc)
            
            is_empty = len(tokens) == 0
            
            return StyleProfile(
                doc_id=doc_id,
                source_path=source_path,
                style_counts=style_counts,
                style_sequence=style_sequence,
                tokens=tokens,
                n_pages=n_pages,
                is_empty=is_empty
            )
        except Exception as e:
            return StyleProfile(
                doc_id=doc_id,
                source_path=source_path,
                error=f"Extraction failed: {str(e)}"
            )
        finally:
            doc.close()

    def extract_batch(
        self, 
        sources: list[str | Path | bytes], 
        doc_ids: list[str]
    ) -> list[StyleProfile]:
        """
        Extract style profiles from multiple PDFs.
        
        Args:
            sources: List of paths or bytes
            doc_ids: List of identifiers (same order as sources)
            
        Returns:
            List of StyleProfile objects
        """
        if len(sources) != len(doc_ids):
            raise ValueError("sources and doc_ids must have same length")
        
        return [
            self.extract(src, did) 
            for src, did in zip(sources, doc_ids)
        ]

    def _extract_styles(self, doc: fitz.Document) -> tuple[dict, list, list, int]:
        """
        Core extraction logic. Iterates through document spans.
        
        Returns:
            Tuple of (style_counts, style_sequence, tokens, n_pages_processed)
        """
        style_counts = {}
        style_sequence = []
        all_tokens = []
        
        pages_to_process = doc.page_count
        if self.n_pages is not None:
            pages_to_process = min(self.n_pages, doc.page_count)

        for page_num in range(pages_to_process):
            page = doc[page_num]
            page.clean_contents()
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block["type"] != 0:  # Skip non-text blocks
                    continue
                    
                for line in block["lines"]:
                    for span in line["spans"]:
                        if not span["text"].strip():
                            continue
                        
                        # Extract style attributes
                        decomposed = self._decompose_style(span)
                        composite = self._composite_style(span)
                        
                        # Update counts
                        for token in decomposed:
                            style_counts[token] = style_counts.get(token, 0) + 1
                        
                        # Append to sequence and token list
                        style_sequence.append(composite)
                        all_tokens.extend(decomposed)

        return style_counts, style_sequence, all_tokens, pages_to_process

    def _decompose_style(self, span: dict) -> list[str]:
        """
        Convert span to decomposed tokens.
        
        Produces: ["sz_12.0", "font_Arial", "flag_bold", "color_000000"]
        """
        tokens = []
        
        # Font size (rounded to 1 decimal)
        size = round(span["size"], 1)
        tokens.append(f"sz_{size}")
        
        # Font family (normalized)
        font = self._normalize_font_name(span["font"])
        tokens.append(f"font_{font}")
        
        # Flags (bold, italic, etc.)
        flag_tokens = self._parse_flags(span["flags"])
        tokens.extend(flag_tokens)
        
        # Color (as hex)
        color_hex = self._color_to_hex(span["color"])
        tokens.append(f"color_{color_hex}")
        
        return tokens

    def _composite_style(self, span: dict) -> str:
        """
        Create composite style identifier for sequence tracking.
        
        Produces: "sz12.0_Arial_bold_000000"
        """
        size = round(span["size"], 1)
        font = self._normalize_font_name(span["font"])
        flags = "_".join(self._parse_flags(span["flags"])).replace("flag_", "")
        color = self._color_to_hex(span["color"])
        
        if flags:
            return f"sz{size}_{font}_{flags}_{color}"
        else:
            return f"sz{size}_{font}_{color}"

    def _normalize_font_name(self, font: str) -> str:
        """
        Normalize font name for consistent tokenization.
        
        Handles variants like "Arial-BoldMT" → "Arial"
        """
        # Remove common suffixes
        normalized = font.split("-")[0].split(",")[0]
        # Remove style indicators often embedded in name
        for suffix in ["MT", "PS", "Bold", "Italic", "Regular", "Light", "Medium"]:
            if normalized.endswith(suffix) and len(normalized) > len(suffix):
                normalized = normalized[:-len(suffix)]
        return normalized or font

    def _parse_flags(self, flags: int) -> list[str]:
        """
        Parse PyMuPDF font flags into readable tokens.
        
        Flags are a bitmask:
        - bit 0: superscript
        - bit 1: italic
        - bit 2: serifed
        - bit 3: monospaced
        - bit 4: bold
        """
        tokens = []
        if flags & (1 << 4):
            tokens.append("flag_bold")
        if flags & (1 << 1):
            tokens.append("flag_italic")
        if flags & (1 << 2):
            tokens.append("flag_serif")
        if flags & (1 << 3):
            tokens.append("flag_mono")
        if flags & (1 << 0):
            tokens.append("flag_super")
        
        # If no flags, indicate regular
        if not tokens:
            tokens.append("flag_regular")
        
        return tokens

    def _color_to_hex(self, color: int) -> str:
        """Convert integer color to hex string."""
        return f"{color:06x}"

    def _is_valid_pdf(self, data: bytes) -> bool:
        """Check if data starts with PDF magic bytes."""
        return data[:5] == b'%PDF-'