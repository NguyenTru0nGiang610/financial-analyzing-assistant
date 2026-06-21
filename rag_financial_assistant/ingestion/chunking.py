import re


SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text, chunk_size=400, overlap=50):
    return _chunk_units([text], chunk_size, overlap)


def _normalize_whitespace(text):
    return re.sub(r"[ \t]+", " ", text).strip()


def _section_prefix(doc):
    title = (doc.get("section_title") or "").strip()
    section_type = (doc.get("section_type") or "").strip()

    if not title:
        return ""

    if section_type and section_type != "body":
        return f"{title}\n[{section_type}]"

    return title


def _split_paragraphs(text):
    paragraphs = []
    for block in re.split(r"\n\s*\n", text):
        cleaned = _normalize_whitespace(block.replace("\n", " "))
        if cleaned:
            paragraphs.append(cleaned)
    return paragraphs


def _split_sentences(text):
    sentences = []
    for part in SENTENCE_BOUNDARY_RE.split(text):
        cleaned = _normalize_whitespace(part)
        if cleaned:
            sentences.append(cleaned)
    return sentences or [_normalize_whitespace(text)]


def _split_words(text, max_length):
    words = text.split()
    if not words:
        return []

    fragments = []
    current = []
    current_length = 0
    target_size = max(1, min(max_length, 120))

    for word in words:
        additional = len(word) if not current else len(word) + 1
        if current and current_length + additional > target_size:
            fragments.append(" ".join(current))
            current = [word]
            current_length = len(word)
        else:
            current.append(word)
            current_length += additional

    if current:
        fragments.append(" ".join(current))

    return fragments


def _split_oversized_unit(unit, max_length):
    normalized = _normalize_whitespace(unit)
    if len(normalized) <= max_length:
        return [normalized] if normalized else []

    if "\n" in unit:
        pieces = []
        for line in unit.splitlines():
            cleaned = _normalize_whitespace(line)
            if not cleaned:
                continue
            if len(cleaned) <= max_length:
                pieces.append(cleaned)
            else:
                pieces.extend(_split_oversized_unit(cleaned, max_length))
        return pieces

    sentences = _split_sentences(normalized)
    if len(sentences) > 1:
        pieces = []
        for sentence in sentences:
            if len(sentence) <= max_length:
                pieces.append(sentence)
            else:
                pieces.extend(_split_words(sentence, max_length))
        return pieces

    return _split_words(normalized, max_length)


def _chunk_units(units, chunk_size, overlap, prefix=""):
    prefix = prefix.strip()
    prefix_length = len(prefix) + 2 if prefix else 0
    available_size = max(chunk_size - prefix_length, 1)
    expanded_units = []

    for unit in units:
        normalized = unit.strip()
        if not normalized:
            continue

        if len(normalized) > available_size:
            expanded_units.extend(_split_oversized_unit(normalized, available_size))
        else:
            expanded_units.append(normalized)

    chunks = []
    current_units = []
    current_length = 0

    for unit in expanded_units:
        unit_length = len(unit) if not current_units else len(unit) + 2
        if current_units and current_length + unit_length > available_size:
            chunks.append("\n\n".join(current_units))
            current_units = _overlap_tail(current_units, overlap, available_size)
            current_length = len("\n\n".join(current_units)) if current_units else 0

        if current_units:
            current_length += len(unit) + 2
        else:
            current_length = len(unit)
        current_units.append(unit)

    if current_units:
        chunks.append("\n\n".join(current_units))

    if prefix:
        return [f"{prefix}\n\n{chunk}".strip() for chunk in chunks if chunk.strip()]

    return [chunk for chunk in chunks if chunk.strip()]


def _overlap_tail(units, overlap, max_length):
    if overlap <= 0 or not units:
        return []

    kept = []
    kept_length = 0

    for unit in reversed(units):
        additional = len(unit) if not kept else len(unit) + 2
        if kept and kept_length + additional > min(overlap, max_length):
            break
        if not kept and len(unit) > max_length:
            break
        kept.append(unit)
        kept_length += additional

    return list(reversed(kept))


def _units_for_table(text, chunk_size, overlap):
    lines = [_normalize_whitespace(l) for l in text.splitlines() if l.strip()]
    if not lines:
        return []

    header = lines[0]        
    data_rows = lines[1:]

    chunks = []
    current_rows = []
    current_length = len(header)

    for row in data_rows:
        # +2 for the \n\n separator
        if current_rows and current_length + len(row) + 2 > chunk_size - len(header) - 2:
            chunks.append(header + "\n" + "\n".join(current_rows))
            # overlap: carry last N rows into the next chunk
            current_rows = current_rows[-overlap:] if overlap else []
            current_length = len(header) + sum(len(r) + 1 for r in current_rows)

        current_rows.append(row)
        current_length += len(row) + 1

    if current_rows:
        chunks.append(header + "\n" + "\n".join(current_rows))

    return chunks

def _sentence_chunks(text, chunk_size, overlap):
    sentences = _split_sentences(text)
    chunks = []
    start = 0

    while start < len(sentences):
        current_chunk = []
        current_length = 0

        for i in range(start, len(sentences)):
            s = sentences[i]
            if current_chunk and current_length + len(s) + 1 > chunk_size:
                break
            current_chunk.append(s)
            current_length += len(s) + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        # find how many sentences to step forward (chunk_size - overlap)
        step_length = 0
        step = 0
        for s in current_chunk:
            if step_length + len(s) >= max(chunk_size - overlap, 1):
                break
            step_length += len(s) + 1
            step += 1

        start += max(step, 1)  # always advance at least 1 sentence

    return chunks

def _units_for_document(doc, chunk_size=400, overlap=50):
    text = doc["text"].strip()
    section_type = (doc.get("section_type") or "body").strip().lower()

    if section_type == "table":
        # Returns pre-assembled chunks with header pinned — skip _chunk_units
        return _units_for_table(text, chunk_size, overlap)

    paragraphs = _split_paragraphs(text)

    # If a single paragraph is large, split it by sentence with overlap
    expanded = []
    for para in paragraphs:
        if len(para) > chunk_size:
            expanded.extend(_sentence_chunks(para, chunk_size, overlap))
        else:
            expanded.append(para)

    return expanded or _split_sentences(text) or [_normalize_whitespace(text)]


def chunk_documents(documents, chunk_size, overlap):
    chunked_docs = []

    for doc_index, doc in enumerate(documents):
        text = doc["text"].strip()

        if not text:
            continue

        prefix = _section_prefix(doc)
        raw_chunks = _chunk_units(
            _units_for_document(doc),
            chunk_size,
            overlap,
            prefix=prefix,
        )

        for chunk_index, chunk in enumerate(raw_chunks):
            chunked_docs.append(
                {
                    "text": chunk,
                    "source": doc["source"],
                    "page": doc["page"],
                    "chunk_id": f"{doc_index}-{chunk_index}",
                    "section_title": doc.get("section_title"),
                    "section_type": doc.get("section_type", "body"),
                }
            )

    return chunked_docs
