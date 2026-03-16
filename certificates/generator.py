import textwrap


def _escape_pdf_text(value):
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf(objects):
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(obj.encode("latin-1"))
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF"
        ).encode("latin-1")
    )
    return bytes(pdf)


def generate_certificate_pdf(student_name, course_title, issued_at, certificate_number, badge_name=""):
    date_text = issued_at.strftime("%B %d, %Y")
    lines = [
        (28, "Certificate of Completion"),
        (14, "This certifies that"),
        (24, student_name),
        (14, "has successfully completed the course"),
        (20, course_title),
        (12, f"Issued on {date_text}"),
        (12, f"Certificate No. {certificate_number}"),
    ]
    if badge_name:
        lines.append((12, f"Badge Earned: {badge_name}"))

    content_lines = []
    current_y = 720
    for font_size, text in lines:
        wrapped = textwrap.wrap(text, width=48) or [text]
        for segment in wrapped:
            content_lines.extend(
                [
                    "BT",
                    f"/F1 {font_size} Tf",
                    f"72 {current_y} Td",
                    f"({_escape_pdf_text(segment)}) Tj",
                    "ET",
                ]
            )
            current_y -= font_size + 18
        current_y -= 12

    stream = "\n".join(content_lines)
    stream_object = f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        stream_object,
    ]
    return _build_pdf(objects)
