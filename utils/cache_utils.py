from ema_scraper import settings
import ast
from typing import List, Union, Tuple
from pathlib import Path

BASE_PATH = settings.BASE_PATH.expanduser()
CACHE_PATH = BASE_PATH.joinpath("cache").joinpath("ema-sitemap")

PdfEntry = Tuple[Path, str]          # (cache_path, url)
FailedEntry = Tuple[Path, Exception] # (cache_path, error)

def get_pdfs_from_cache() -> Tuple[List[PdfEntry], List[FailedEntry]]:
    """
    Returns paths to all pdf files in the scrapy cache
    """
    pdf_entries = []
    failed = []
    for root, directories, filenames in CACHE_PATH.walk():
        if filenames and "meta" in filenames:
            try:
                with open(root.joinpath("meta"), "r") as f:
                    meta = ast.literal_eval(f.read())
                if meta.get("url", "").endswith(".pdf"):
                    pdf_entries.append((root, meta["url"]))
            except Exception as e:
                failed.append((root, e))
    return pdf_entries, failed

def get_files_from_cache(file_name: str) -> List[str]:
    """
    Returns paths to all files in the scrapy cache
    """
    file_entries = []
    for root, directories, filenames in CACHE_PATH.walk():
        if filenames and root.joinpath(file_name).exists():
            file_entries.append(root.joinpath(file_name))
    return file_entries