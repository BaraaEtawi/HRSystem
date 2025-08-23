from __future__ import annotations
import re
from typing import List, Dict


def split_markdown(text: str, max_chars: int = 1000, overlap: int = 150) -> List[Dict]:

    text = text.replace("\r\n", "\n").strip()
    parts: List[Dict] = []
    current_heading = ""
    buffer: List[str] = []

    for line in text.split("\n"):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            if buffer:
                section_text = "\n".join(buffer).strip()
                if section_text:
                    parts.extend(_window(section_text, current_heading, max_chars, overlap))
                buffer = []
            current_heading = m.group(2).strip()
            buffer.append(line)
        else:
            buffer.append(line)

    if buffer:
        section_text = "\n".join(buffer).strip()
        if section_text:
            parts.extend(_window(section_text, current_heading, max_chars, overlap))

    return parts


def _window(section: str, heading: str, max_chars: int, overlap: int) -> List[Dict]:
    chunks: List[Dict] = []
    if len(section) <= max_chars:
        return [{"content": section, "heading": heading}]

    start = 0
    while start < len(section):
        end = min(start + max_chars, len(section))
        chunk = section[start:end]
        chunks.append({"content": chunk, "heading": heading})
        if end == len(section):
            break
        start = max(0, end - overlap)
    return chunks