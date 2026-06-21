# import re
# from io import BytesIO

# from pypdf import PdfReader


# HEADING_RE = re.compile(r"^(\d+(\.\d+)*)[\s.)-]+[A-Z].*")


# def _extract_page_text(page):
#     try:
#         text = page.extract_text(extraction_mode="layout")
#     except TypeError:
#         text = page.extract_text()

#     return text or ""


# def _normalize_block(block):
#     lines = [line.rstrip() for line in block.splitlines()]
#     cleaned = [line for line in lines if line.strip()]
#     return "\n".join(cleaned).strip()


# def _is_heading(block):
#     if "\n" in block:
#         return False

#     line = block.strip()
#     if not line or len(line) > 120:
#         return False

#     if HEADING_RE.match(line):
#         return True

#     words = line.split()
#     if not words or len(words) > 12:
#         return False

#     uppercase_ratio = sum(1 for char in line if char.isupper()) / max(sum(1 for char in line if char.isalpha()), 1)
#     titlecase_words = sum(1 for word in words if word[:1].isupper())

#     return uppercase_ratio > 0.7 or titlecase_words / len(words) > 0.8


# def _is_table_block(block):
#     lines = [line for line in block.splitlines() if line.strip()]
#     if len(lines) < 2:
#         return False

#     numeric_lines = sum(1 for line in lines if re.search(r"\d", line))
#     multi_space_lines = sum(1 for line in lines if re.search(r"\S\s{2,}\S", line))

#     return numeric_lines >= max(2, len(lines) // 2) and multi_space_lines >= max(1, len(lines) // 3)


# def _section_type_from_heading(heading):
#     normalized = heading.lower()

#     if "conclusion" in normalized or "summary" in normalized:
#         return "conclusion"
#     if "table" in normalized or "schedule" in normalized:
#         return "table"

#     return "body"


# def _table_title(block, fallback_heading=None):
#     first_line = next((line.strip() for line in block.splitlines() if line.strip()), "")

#     if first_line and len(first_line) <= 140:
#         return first_line

#     return fallback_heading or "Table"


# def _make_section(text, source, page, section_title=None, section_type="body"):
#     normalized = " ".join(text.split())
#     if not normalized:
#         return None

#     return {
#         "text": normalized,
#         "source": source,
#         "page": page,
#         "section_title": section_title,
#         "section_type": section_type,
#     }


# def extract_sections_from_pdf(pdf_bytes, source):
#     reader = PdfReader(BytesIO(pdf_bytes))
#     sections = []
#     current_heading = None
#     current_type = "body"
#     buffered_paragraphs = []
#     buffer_page = 0

#     def flush_buffer():
#         nonlocal buffered_paragraphs, buffer_page

#         if not buffered_paragraphs:
#             return

#         merged = "\n\n".join(buffered_paragraphs)
#         section = _make_section(
#             merged,
#             source=source,
#             page=buffer_page,
#             section_title=current_heading,
#             section_type=current_type,
#         )
#         if section:
#             sections.append(section)
#         buffered_paragraphs = []

#     for page_number, page in enumerate(reader.pages):
#         page_text = _extract_page_text(page)
#         if not page_text.strip():
#             continue

#         blocks = [_normalize_block(block) for block in re.split(r"\n\s*\n", page_text)]
#         blocks = [block for block in blocks if block]

#         for block in blocks:
#             if _is_heading(block):
#                 flush_buffer()
#                 current_heading = block
#                 current_type = _section_type_from_heading(block)
#                 buffer_page = page_number
#                 continue

#             if _is_table_block(block):
#                 flush_buffer()
#                 table_title = _table_title(block, current_heading)
#                 section = _make_section(
#                     block,
#                     source=source,
#                     page=page_number,
#                     section_title=table_title,
#                     section_type="table",
#                 )
#                 if section:
#                     sections.append(section)
#                 continue

#             if not buffered_paragraphs:
#                 buffer_page = page_number
#             buffered_paragraphs.append(block)

#     flush_buffer()
#     return sections


# def extract_sections_from_text(text, source):
#     section = _make_section(text, source=source, page=0)
#     return [section] if section else []


# def extract_documents(file_bytes, source):
#     if source.lower().endswith(".pdf"):
#         sections = extract_sections_from_pdf(file_bytes, source)
#         if sections:
#             return sections

#     try:
#         text = file_bytes.decode("utf-8", errors="ignore")
#     except AttributeError:
#         text = str(file_bytes)

#     return extract_sections_from_text(text, source)
import fitz
import re

def _make_section(text, source, page, section_title=None, section_type="body"):
    paragraphs = []
    for block in re.split(r"\n\s*\n", text):
        lines = [re.sub(r"\s+", " ", line).strip() for line in block.splitlines()]
        compact = " ".join(line for line in lines if line).strip()
        if compact:
            paragraphs.append(compact)

    normalized = "\n\n".join(paragraphs).strip()
    if not normalized:
        return None

    return {
        "text": normalized,
        "source": source,
        "page": page,
        "section_title": section_title,
        "section_type": section_type,
    }
def extract_sections_from_pdf(source):
    doc = fitz.open(source)
    sections = []
    for page_number, page in enumerate(doc):
        #
        # 1. Extract Tables
        #
        try:
            tables = page.find_tables()
            for table_idx, table in enumerate(tables.tables):
                data = table.extract()
                if not data:
                    continue
                header = " | ".join(str(cell or "") for cell in data[0])
                rows = [
                    " | ".join(
                        str(cell or "")
                        for cell in row
                    )
                    for row in data[1:]
                ]

                table_text = (
                    header +
                    "\n" +
                    "\n".join(rows)
                )

                sections.append(
                    {
                        "text": table_text,
                        "source": source,
                        "page": page_number,
                        "section_title": f"table_{table_idx}",
                        "section_type": "table",
                    }
                )

        except Exception as e:
            print(
                f"Table extraction failed on page "
                f"{page_number}: {e}"
            )
        blocks = page.get_text("blocks")

        text_blocks = []

        for block in blocks:

            text = block[4]

            if not text:
                continue

            cleaned = text.strip()

            if not cleaned:
                continue

            text_blocks.append(cleaned)

        page_text = "\n\n".join(text_blocks)

        section = _make_section(
            page_text,
            source=source,
            page=page_number,
            section_type="body",
        )

        if section:
            sections.append(section)

    return sections

def extract_documents(source):
    sections = extract_sections_from_pdf(source)
    if sections:
        return sections
    else:
        print(f"No text extracted from PDF: {source}")
        return []