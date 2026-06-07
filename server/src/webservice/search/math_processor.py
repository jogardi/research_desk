"""
Math processing utility for preparing TeX in document chunks for frontend rendering.
Currently normalizes/wraps TeX for KaTeX auto-render on the client.
"""

import re
from typing import List, Dict, Union

# Try to import shared logger, fallback to print if not available
try:
    from shared.logger import Logger
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False
    # Simple fallback logger
    class FallbackLogger:
        def info(self, msg):
            print(f"[INFO] {msg}")
        def warning(self, msg):
            print(f"[WARNING] {msg}")
        def error(self, msg):
            print(f"[ERROR] {msg}")
    
    Logger = FallbackLogger()

# HTML parsing for bare-TeX detection
try:
    from bs4 import BeautifulSoup, NavigableString
    BS4_AVAILABLE = True
except Exception:
    BS4_AVAILABLE = False


def _contains_math_delimiters(text: str) -> bool:
    return bool(re.search(r"\$|\\\(|\\\[", text))


def _is_probably_math_block(text: str) -> bool:
    # Heuristics: presence of common TeX commands or subscripts/superscripts, or equation-like with '='
    has_tex_cmd = re.search(r"\\(sum|frac|int|sqrt|alpha|beta|gamma|delta|theta|lambda|mu|nu|pi|phi|psi|left|right|times|cdot|leq|geq)", text)
    has_subsup = re.search(r"[A-Za-z0-9]\s*[_^]\s*[A-Za-z0-9]", text)
    looks_equation = re.search(r"^\s*(?:[A-Za-z]|\\)[^\n<]*=", text)
    # Avoid wrapping if there are many plain words (likely prose)
    plain_words = re.findall(r"[A-Za-z]{3,}", text)
    return bool((has_tex_cmd or has_subsup or looks_equation) and (len(plain_words) <= 12))


def _wrap_bare_math_blocks(html: str) -> str:
    if not BS4_AVAILABLE:
        return html
    try:
        soup = BeautifulSoup(html, 'html.parser')
        wrapped = 0
        for p in soup.find_all('p'):
            if p.find('script', attrs={'type': re.compile('^math/tex')}):
                continue
            p_text = p.get_text(strip=True)
            if not p_text:
                continue
            if _contains_math_delimiters(p_text):
                continue
            if any(not isinstance(c, NavigableString) for c in p.contents):
                continue
            if _is_probably_math_block(p_text):
                # Wrap as KaTeX block delimiter
                p.string = f"$$ {p_text} $$"
                wrapped += 1
        if wrapped:
            try:
                Logger.info(f"Wrapped {wrapped} bare math block(s) with display delimiters ($$)")
            except Exception:
                print(f"[INFO] Wrapped {wrapped} bare math block(s) with display delimiters ($$)")
        return str(soup)
    except Exception as e:
        try:
            Logger.warning(f"Bare math wrapping failed: {e}")
        except Exception:
            print(f"[WARNING] Bare math wrapping failed: {e}")
        return html


def _convert_bracket_delimiters_to_dollars(html: str) -> str:
    if not BS4_AVAILABLE:
        # Fallback: regex on whole string
        html = re.sub(r"\\\[(.+?)\\\]", r"$$ \1 $$", html, flags=re.S)
        html = re.sub(r"\\\((.+?)\\\)", r"$ \1 $", html, flags=re.S)
        return html
    try:
        soup = BeautifulSoup(html, 'html.parser')
        for text_node in list(soup.find_all(string=True)):
            if text_node.parent and text_node.parent.name in ('script', 'style'):
                continue
            txt = str(text_node)
            original = txt
            txt = re.sub(r"\\\[(.+?)\\\]", r"$$ \1 $$", txt, flags=re.S)
            txt = re.sub(r"\\\((.+?)\\\)", r"$ \1 $", txt, flags=re.S)
            if txt != original:
                text_node.replace_with(NavigableString(txt))
        return str(soup)
    except Exception as e:
        try:
            Logger.warning(f"Bracket-to-dollar conversion failed: {e}")
        except Exception:
            print(f"[WARNING] Bracket-to-dollar conversion failed: {e}")
        return html


def process_math_in_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Prepare TeX for KaTeX auto-render on the client.
    - Wrap bare TeX paragraphs as $$ ... $$ (display)
    - Normalize \[...]/\(...\) to $$...$$/$...$
    """
    try:
        print(f"*** Processing math in {len(chunks)} chunks ***")
        processed_count = 0
        error_count = 0
        processed_chunks = []

        for chunk in chunks:
            chunk_copy = chunk.copy()
            processed_chunks.append(chunk_copy)

            if 'text' in chunk_copy and chunk_copy['text']:
                try:
                    text = chunk_copy['text']
                    # 1) Wrap bare TeX blocks inside <p> as $$ ... $$
                    text = _wrap_bare_math_blocks(text)
                    # 2) Convert \[...]/\(...\) delimiters to $$...$$/$...$ for KaTeX auto-render
                    text = _convert_bracket_delimiters_to_dollars(text)
                    chunk_copy['text'] = text
                    processed_count += 1
                except Exception as e:
                    error_count += 1
                    try:
                        Logger.warning(f"Failed to process math in chunk {chunk_copy.get('id', 'unknown')}: {e}")
                    except Exception:
                        print(f"[WARNING] Failed to process math in chunk {chunk_copy.get('id', 'unknown')}: {e}")
                    continue

        try:
            if processed_count > 0:
                Logger.info(f"Prepared KaTeX delimiters in {processed_count} chunks")
            if error_count > 0:
                Logger.warning(f"Failed to prepare KaTeX delimiters in {error_count} chunks")
        except Exception:
            if processed_count > 0:
                print(f"[INFO] Prepared KaTeX delimiters in {processed_count} chunks")
            if error_count > 0:
                print(f"[WARNING] Failed to prepare KaTeX delimiters in {error_count} chunks")

    except Exception as e:
        try:
            Logger.error(f"Error during KaTeX preparation: {e}")
        except Exception:
            print(f"[ERROR] Error during KaTeX preparation: {e}")
        return chunks

    return processed_chunks


def process_math_in_documents(documents: List[Dict]) -> List[Dict]:
    """
    Prepare TeX in document chunks for KaTeX auto-render on the client.
    """
    print(f"*** Processing math in {len(documents)} documents ***")

    processed_documents = []
    for doc in documents:
        doc_copy = doc.copy()
        processed_documents.append(doc_copy)
        if 'chunks' in doc_copy and doc_copy['chunks']:
            doc_copy['chunks'] = process_math_in_chunks(doc_copy['chunks'])
    return processed_documents


def has_math_content(text: str) -> bool:
    if not text:
        return False
    math_patterns = [
        r'\$[^$]+\$',
        r'\$\$[^$]+\$\$',
        r'\\\([^)]+\\\)',
        r'\\\[[^\]]+\\\]',
        r'\\begin\{[^}]+\}',
        r'\\end\{[^}]+\}',
    ]
    for pattern in math_patterns:
        if re.search(pattern, text):
            return True
    return False


def get_math_processing_status() -> Dict[str, Union[bool, str]]:
    """
    Legacy status API kept for compatibility with tests.
    For KaTeX-prep flow, server does not depend on python-markdown.
    """
    return {
        'available': False,
        'markdown_version': None,
        'math_extension_version': None,
    } 