"""
Text Extraction - URL, PDF, and file content extraction.

Supports multiple sources with graceful fallback:
- URL: trafilatura → requests + regex stripping
- PDF: pymupdf4llm → pymupdf (fitz)
- File: direct read
- Stdin: piped input
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ExtractedDocument:
    """Result of text extraction."""
    text: str
    source: str
    source_type: str  # "url", "pdf", "file", "stdin"
    title: Optional[str] = None
    word_count: int = 0
    error: Optional[str] = None

    def __post_init__(self):
        if self.text and not self.word_count:
            self.word_count = len(self.text.split())


def extract_text(source: str) -> ExtractedDocument:
    """
    Extract text from a source (URL, PDF path, file path, or "-" for stdin).

    Args:
        source: URL, file path, or "-" for stdin

    Returns:
        ExtractedDocument with extracted text
    """
    if source == "-":
        return _extract_stdin()
    elif source.startswith(("http://", "https://")):
        return _extract_url(source)
    elif source.lower().endswith(".pdf"):
        return _extract_pdf(source)
    else:
        return _extract_file(source)


def _extract_stdin() -> ExtractedDocument:
    """Read from stdin."""
    import sys
    try:
        text = sys.stdin.read()
        return ExtractedDocument(
            text=text.strip(),
            source="stdin",
            source_type="stdin",
            title="stdin input",
        )
    except Exception as e:
        return ExtractedDocument(
            text="", source="stdin", source_type="stdin",
            error=f"stdin read failed: {e}",
        )


def _extract_url(url: str) -> ExtractedDocument:
    """Extract text from URL using trafilatura with requests fallback."""
    # Try trafilatura first
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            )
            if text:
                # Try to get title
                title = None
                try:
                    metadata = trafilatura.extract_metadata(downloaded)
                    if metadata:
                        title = metadata.title
                except Exception:
                    pass

                return ExtractedDocument(
                    text=text,
                    source=url,
                    source_type="url",
                    title=title,
                )
    except ImportError:
        logger.debug("trafilatura not available, falling back to requests")
    except Exception as e:
        logger.debug(f"trafilatura extraction failed: {e}")

    # Fallback: requests + regex HTML stripping
    try:
        import requests
        response = requests.get(url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0 (compatible; Empirica/1.5)"
        })
        response.raise_for_status()
        html = response.text

        # Extract title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else None

        # Strip HTML tags
        text = _strip_html(html)

        return ExtractedDocument(
            text=text,
            source=url,
            source_type="url",
            title=title,
        )
    except Exception as e:
        return ExtractedDocument(
            text="", source=url, source_type="url",
            error=f"URL extraction failed: {e}",
        )


def _extract_pdf(path: str) -> ExtractedDocument:
    """Extract text from PDF using pymupdf4llm with pymupdf fallback."""
    import os
    if not os.path.exists(path):
        return ExtractedDocument(
            text="", source=path, source_type="pdf",
            error=f"File not found: {path}",
        )

    # Try pymupdf4llm first (better markdown output)
    try:
        import pymupdf4llm
        text = pymupdf4llm.to_markdown(path)
        if text:
            return ExtractedDocument(
                text=text,
                source=path,
                source_type="pdf",
                title=os.path.basename(path),
            )
    except ImportError:
        logger.debug("pymupdf4llm not available, falling back to pymupdf")
    except Exception as e:
        logger.debug(f"pymupdf4llm failed: {e}")

    # Fallback: pymupdf (fitz)
    try:
        import fitz  # pymupdf
        doc = fitz.open(path)
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        text = "\n\n".join(pages)
        return ExtractedDocument(
            text=text,
            source=path,
            source_type="pdf",
            title=os.path.basename(path),
        )
    except ImportError:
        return ExtractedDocument(
            text="", source=path, source_type="pdf",
            error="No PDF library available (install pymupdf4llm or pymupdf)",
        )
    except Exception as e:
        return ExtractedDocument(
            text="", source=path, source_type="pdf",
            error=f"PDF extraction failed: {e}",
        )


def _extract_file(path: str) -> ExtractedDocument:
    """Read text from a local file."""
    import os
    if not os.path.exists(path):
        return ExtractedDocument(
            text="", source=path, source_type="file",
            error=f"File not found: {path}",
        )
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        return ExtractedDocument(
            text=text,
            source=path,
            source_type="file",
            title=os.path.basename(path),
        )
    except Exception as e:
        return ExtractedDocument(
            text="", source=path, source_type="file",
            error=f"File read failed: {e}",
        )


def _strip_html(html: str) -> str:
    """Strip HTML tags and normalize whitespace. Simple regex-based fallback."""
    # Remove script and style blocks
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode common entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text
