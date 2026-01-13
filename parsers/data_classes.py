from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class Link:
    text: str
    href: str


@dataclass
class HeadingBlock:
    type: str = field(default="heading", init=False)
    level: int = 1
    text: str = ""


@dataclass
class ParagraphBlock:
    type: str = field(default="paragraph", init=False)
    text: str = ""


@dataclass
class ListBlock:
    type: str = field(default="list", init=False)
    ordered: bool = False
    items: list = field(default_factory=list)


@dataclass
class TableBlock:
    type: str = field(default="table", init=False)
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)


@dataclass
class FileBlock:
    type: str = field(default="file", init=False)
    title: str = ""
    reference_number: Optional[str] = None
    document_type: Optional[str] = None
    language: Optional[str] = None
    file_size: Optional[str] = None
    file_format: Optional[str] = None
    first_published: Optional[str] = None
    last_updated: Optional[str] = None
    url: Optional[str] = None


@dataclass
class DescriptionListBlock:
    type: str = field(default="description_list", init=False)
    items: list[list[str]] = field(default_factory=list)  # [[term, description], ...]


@dataclass
class BlockquoteBlock:
    type: str = field(default="blockquote", init=False)
    content: list = field(default_factory=list)  # nested blocks


@dataclass
class BannerBlock:
    type: str = field(default="banner", init=False)
    title: str = ""
    summary: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None


@dataclass
class DateBlock:
    type: str = field(default="date", init=False)
    date: str = ""  # ISO date from datetime attribute
    display_text: Optional[str] = None  # e.g. "08 Jan 2026"


@dataclass
class CardBlock:
    type: str = field(default="card", init=False)
    title: str = ""
    text: Optional[str] = None
    link_url: Optional[str] = None
    image_url: Optional[str] = None
    metadata: Optional[list[str]] = None  # dates, categories, etc.


@dataclass
class ListingBlock:
    type: str = field(default="listing", init=False)
    variant: Optional[str] = None  # e.g. "highlight-3-col", "default-2-col"
    items: list = field(default_factory=list)  # list of CardBlocks


@dataclass
class AlertBlock:
    type: str = field(default="alert", init=False)
    variant: Optional[str] = None  # info, warning, danger, success
    message: str = ""


@dataclass
class AccordionItem:
    title: str = ""
    content: list = field(default_factory=list)


@dataclass
class AccordionBlock:
    type: str = field(default="accordion", init=False)
    items: list[AccordionItem] = field(default_factory=list)