from __future__ import annotations

from io import BytesIO


def _escape_pdf_text(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_text(text: object, max_chars: int = 92) -> list[str]:
    words = str(text or "").split()
    if not words:
        return [""]

    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word[:max_chars]
    if current:
        lines.append(current)
    return lines


def build_simple_pdf(title: str, lines: list[str]) -> bytes:
    """Build a compact text PDF without requiring an external dependency."""

    width = 595
    height = 842
    margin_x = 48
    top_y = 790
    line_height = 15
    bottom_y = 48

    pages: list[list[tuple[int, str, bool]]] = []
    current_page: list[tuple[int, str, bool]] = []
    y = top_y

    def add_line(text: str, bold: bool = False) -> None:
        nonlocal current_page, y
        if y < bottom_y:
            pages.append(current_page)
            current_page = []
            y = top_y
        current_page.append((y, text, bold))
        y -= line_height

    add_line(title, True)
    add_line("")

    for line in lines:
        if line == "":
            add_line("")
            continue
        is_heading = line.startswith("## ")
        content = line[3:] if is_heading else line
        for wrapped in _wrap_text(content, 88):
            add_line(wrapped, is_heading)

    if current_page:
        pages.append(current_page)

    objects: list[bytes] = []

    def add_object(content: bytes) -> int:
        objects.append(content)
        return len(objects)

    catalog_id = add_object(b"")
    pages_id = add_object(b"")
    font_regular_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    page_ids: list[int] = []

    for page in pages:
        stream_parts = ["BT"]
        for line_y, text, bold in page:
            font_name = "F2" if bold else "F1"
            font_size = 13 if bold else 10
            escaped = _escape_pdf_text(text)
            stream_parts.append(f"/{font_name} {font_size} Tf 1 0 0 1 {margin_x} {line_y} Tm ({escaped}) Tj")
        stream_parts.append("ET")
        stream = "\n".join(stream_parts).encode("latin-1", errors="replace")
        stream_id = add_object(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {width} {height}] "
                f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> "
                f"/Contents {stream_id} 0 R >>"
            ).encode("ascii")
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[catalog_id - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii")
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")

    output = BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, content in enumerate(objects, start=1):
        offsets.append(output.tell())
        output.write(f"{index} 0 obj\n".encode("ascii"))
        output.write(content)
        output.write(b"\nendobj\n")

    xref_offset = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.write(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        ).encode("ascii")
    )
    return output.getvalue()
