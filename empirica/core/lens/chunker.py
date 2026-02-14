"""
Paragraph-Based Text Chunking with Token Counting.

Splits text into chunks of ~512 tokens with 64-token overlap.
Paragraph-aware: prefers splitting at paragraph boundaries.
Uses tiktoken with graceful fallback to character approximation.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 512
DEFAULT_OVERLAP = 64


@dataclass
class Chunk:
    """A text chunk with metadata."""
    text: str
    index: int
    token_count: int
    char_start: int = 0
    char_end: int = 0


def _get_tokenizer():
    """Get tiktoken encoder with graceful fallback."""
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base")
    except ImportError:
        logger.debug("tiktoken not available, using character approximation")
        return None
    except Exception as e:
        logger.debug(f"tiktoken init failed: {e}")
        return None


def _count_tokens(text: str, tokenizer=None) -> int:
    """Count tokens in text."""
    if tokenizer is not None:
        return len(tokenizer.encode(text))
    # Fallback: ~4 chars per token
    return len(text) // 4


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[Chunk]:
    """
    Split text into overlapping chunks, preferring paragraph boundaries.

    Args:
        text: Input text
        chunk_size: Target tokens per chunk (default 512)
        overlap: Overlap tokens between chunks (default 64)

    Returns:
        List of Chunk objects
    """
    if not text or not text.strip():
        return []

    tokenizer = _get_tokenizer()
    total_tokens = _count_tokens(text, tokenizer)

    # If text fits in one chunk, return as-is
    if total_tokens <= chunk_size:
        return [Chunk(
            text=text.strip(),
            index=0,
            token_count=total_tokens,
            char_start=0,
            char_end=len(text),
        )]

    # Split into paragraphs first
    paragraphs = _split_paragraphs(text)

    # Build chunks from paragraphs
    chunks = []
    current_paragraphs = []
    current_tokens = 0
    char_offset = 0

    for para in paragraphs:
        para_tokens = _count_tokens(para, tokenizer)

        # If single paragraph exceeds chunk_size, split it further
        if para_tokens > chunk_size:
            # Flush current buffer
            if current_paragraphs:
                chunk_text_str = "\n\n".join(current_paragraphs)
                chunks.append(Chunk(
                    text=chunk_text_str,
                    index=len(chunks),
                    token_count=current_tokens,
                    char_start=char_offset,
                    char_end=char_offset + len(chunk_text_str),
                ))
                char_offset += len(chunk_text_str) + 2
                current_paragraphs = []
                current_tokens = 0

            # Split large paragraph by sentences
            sub_chunks = _split_large_paragraph(para, chunk_size, overlap, tokenizer)
            for sc in sub_chunks:
                sc.index = len(chunks)
                sc.char_start = char_offset
                sc.char_end = char_offset + len(sc.text)
                chunks.append(sc)
                char_offset += len(sc.text) + 2
            continue

        # Would adding this paragraph exceed chunk_size?
        if current_tokens + para_tokens > chunk_size and current_paragraphs:
            # Emit current chunk
            chunk_text_str = "\n\n".join(current_paragraphs)
            chunks.append(Chunk(
                text=chunk_text_str,
                index=len(chunks),
                token_count=current_tokens,
                char_start=char_offset,
                char_end=char_offset + len(chunk_text_str),
            ))

            # Overlap: keep last paragraph(s) up to overlap tokens
            overlap_paras = []
            overlap_tokens = 0
            for p in reversed(current_paragraphs):
                p_tokens = _count_tokens(p, tokenizer)
                if overlap_tokens + p_tokens > overlap:
                    break
                overlap_paras.insert(0, p)
                overlap_tokens += p_tokens

            char_offset += len(chunk_text_str) + 2 - sum(len(p) + 2 for p in overlap_paras)
            current_paragraphs = overlap_paras
            current_tokens = overlap_tokens

        current_paragraphs.append(para)
        current_tokens += para_tokens

    # Flush remaining
    if current_paragraphs:
        chunk_text_str = "\n\n".join(current_paragraphs)
        chunks.append(Chunk(
            text=chunk_text_str,
            index=len(chunks),
            token_count=current_tokens,
            char_start=char_offset,
            char_end=char_offset + len(chunk_text_str),
        ))

    # Re-index
    for i, chunk in enumerate(chunks):
        chunk.index = i

    return chunks


def _split_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs (double newline or single newline with indent)."""
    # Split on double newlines
    raw_paras = text.split("\n\n")
    paragraphs = []
    for para in raw_paras:
        stripped = para.strip()
        if stripped:
            paragraphs.append(stripped)
    return paragraphs


def _split_large_paragraph(
    text: str,
    chunk_size: int,
    overlap: int,
    tokenizer,
) -> List[Chunk]:
    """Split a large paragraph into sentence-based chunks."""
    import re
    # Split by sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_sentences = []
    current_tokens = 0

    for sentence in sentences:
        s_tokens = _count_tokens(sentence, tokenizer)

        if current_tokens + s_tokens > chunk_size and current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(Chunk(
                text=chunk_text,
                index=0,
                token_count=current_tokens,
            ))
            # Overlap: keep last sentence(s)
            overlap_sents = []
            ov_tokens = 0
            for s in reversed(current_sentences):
                st = _count_tokens(s, tokenizer)
                if ov_tokens + st > overlap:
                    break
                overlap_sents.insert(0, s)
                ov_tokens += st
            current_sentences = overlap_sents
            current_tokens = ov_tokens

        current_sentences.append(sentence)
        current_tokens += s_tokens

    if current_sentences:
        chunk_text = " ".join(current_sentences)
        chunks.append(Chunk(
            text=chunk_text,
            index=0,
            token_count=current_tokens,
        ))

    return chunks
