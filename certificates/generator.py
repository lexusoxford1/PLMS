import textwrap
from io import BytesIO
from math import cos, pi, sin

from .presentation import build_certificate_view_model

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback only used when dependency is missing
    REPORTLAB_AVAILABLE = False


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


def _generate_basic_pdf(presentation):  # pragma: no cover - only used when ReportLab is unavailable
    lines = [
        (28, presentation["completion_label"]),
        (14, "This certifies that"),
        (24, presentation["learner_name"]),
    ]
    if presentation["learner_identity_line"]:
        lines.append((11, presentation["learner_identity_line"]))
    lines.extend(
        [
            (14, "has successfully completed the course"),
            (20, presentation["course_title"]),
            (12, f"Issued on {presentation['issued_date']}"),
            (12, f"Certificate No. {presentation['certificate_number']}"),
        ]
    )
    if presentation["show_profile_fact"]:
        lines.append((12, f"{presentation['profile_fact_label']}: {presentation['profile_fact_value']}"))
    lines.append((12, f"Signed by {presentation['signatory_name']} - {presentation['signatory_title']}"))
    if presentation["badge_name"]:
        lines.append((12, f"Completion Badge: {presentation['badge_name']}"))

    content_lines = []
    current_y = 720
    for font_size, text in lines:
        wrapped = textwrap.wrap(text, width=50) or [text]
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


def _hex(value):
    return colors.HexColor(value)


def _draw_circle_pattern(pdf, width, height, theme):
    pdf.saveState()
    pdf.setFillColor(_hex(theme["soft"]))
    for row in range(3):
        for column in range(9):
            radius = 16 - row * 2
            x = 86 + column * 38 + (row % 2) * 16
            y = height - 92 - row * 28
            pdf.circle(x, y, radius, fill=1, stroke=0)
    pdf.restoreState()


def _draw_body_pattern(pdf):
    pdf.saveState()
    pdf.setFillColor(_hex("#ebe5d8"))
    for row in range(4):
        for column in range(8):
            x = 92 + column * 58 + (row % 2) * 18
            y = 96 + row * 42
            pdf.ellipse(x, y, x + 22, y + 34, fill=1, stroke=0)
    pdf.restoreState()


def _draw_wave(pdf, width, height, theme):
    header_base = height * 0.59

    pdf.setFillColor(_hex(theme["primary"]))
    pdf.rect(0, header_base, width, height - header_base, fill=1, stroke=0)

    pdf.saveState()
    pdf.setFillColor(colors.white)
    for index in range(5):
        pdf.circle(width - 160 + index * 32, height - 54 - (index % 2) * 14, 10 + (index % 3) * 2, fill=1, stroke=0)
    pdf.restoreState()

    accent = pdf.beginPath()
    accent.moveTo(0, header_base + 12)
    accent.curveTo(width * 0.18, header_base + 44, width * 0.45, header_base - 6, width, header_base + 18)
    accent.lineTo(width, header_base - 6)
    accent.curveTo(width * 0.66, header_base + 4, width * 0.42, header_base - 46, 0, header_base - 18)
    accent.close()
    pdf.setFillColor(_hex(theme["accent"]))
    pdf.drawPath(accent, fill=1, stroke=0)

    body = pdf.beginPath()
    body.moveTo(0, header_base - 8)
    body.curveTo(width * 0.16, header_base + 26, width * 0.52, header_base - 28, width, header_base + 8)
    body.lineTo(width, 0)
    body.lineTo(0, 0)
    body.close()
    pdf.setFillColor(_hex(theme["surface"]))
    pdf.drawPath(body, fill=1, stroke=0)

    pdf.setFillColor(_hex(theme["accent"]))
    pdf.rect(0, 0, width, 8, fill=1, stroke=0)
    pdf.setFillColor(_hex(theme["primary"]))
    pdf.rect(0, 8, width, 6, fill=1, stroke=0)


def _draw_hex_badge(pdf, center_x, center_y, radius, theme, text):
    points = []
    for index in range(6):
        angle = pi / 6 + (pi / 3) * index
        points.extend(
            [
                center_x + radius * cos(angle),
                center_y + radius * sin(angle),
            ]
        )

    inner_points = []
    for index in range(6):
        angle = pi / 6 + (pi / 3) * index
        inner_points.extend(
            [
                center_x + radius * 0.74 * cos(angle),
                center_y + radius * 0.74 * sin(angle),
            ]
        )

    outer_path = pdf.beginPath()
    outer_path.moveTo(points[0], points[1])
    for index in range(2, len(points), 2):
        outer_path.lineTo(points[index], points[index + 1])
    outer_path.close()

    inner_path = pdf.beginPath()
    inner_path.moveTo(inner_points[0], inner_points[1])
    for index in range(2, len(inner_points), 2):
        inner_path.lineTo(inner_points[index], inner_points[index + 1])
    inner_path.close()

    pdf.saveState()
    pdf.setFillColor(_hex(theme["secondary"]))
    pdf.setStrokeColor(colors.white)
    pdf.setLineWidth(2.2)
    pdf.drawPath(outer_path, stroke=1, fill=1)
    pdf.setFillColor(_hex(theme["primary"]))
    pdf.drawPath(inner_path, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", max(12, radius * 0.52))
    pdf.drawCentredString(center_x, center_y - radius * 0.14, text)
    pdf.restoreState()


def _draw_metadata_pill(pdf, x, y, width, label, value, theme):
    pdf.saveState()
    pdf.setFillColor(_hex(theme["surface_tint"]))
    pdf.roundRect(x, y, width, 44, 18, fill=1, stroke=0)
    pdf.setFillColor(_hex(theme["muted"]))
    pdf.setFont("Helvetica-Bold", 8.5)
    pdf.drawString(x + 14, y + 28, label.upper())
    pdf.setFillColor(_hex(theme["ink"]))
    value_lines = simpleSplit(value, "Helvetica-Bold", 10.5, width - 28) or [value]
    pdf.setFont("Helvetica-Bold", 10.5)
    if len(value_lines) > 1:
        pdf.drawString(x + 14, y + 16, value_lines[0])
        pdf.drawString(x + 14, y + 6, value_lines[1])
    else:
        pdf.drawString(x + 14, y + 12, value_lines[0])
    pdf.restoreState()


def _draw_profile_line(pdf, presentation, y_position, theme):
    if not presentation["show_identity_line"]:
        return y_position

    identity_lines = simpleSplit(
        presentation["learner_identity_line"],
        "Helvetica",
        11.5,
        pdf._pagesize[0] - 300,
    )
    if not identity_lines:
        return y_position

    last_y = _draw_centered_block(
        pdf,
        identity_lines,
        y_position,
        "Helvetica",
        11.5,
        16,
        _hex(theme["muted"]),
    )
    return last_y - 8


def _draw_signature(pdf, x, y, width, theme):
    path = pdf.beginPath()
    path.moveTo(x, y)
    path.curveTo(x + 14, y + 18, x + 24, y - 10, x + 38, y + 4)
    path.curveTo(x + 52, y + 20, x + 66, y + 12, x + 80, y + 2)
    path.curveTo(x + 96, y - 8, x + 108, y + 18, x + 124, y + 6)
    path.curveTo(x + 142, y - 8, x + 160, y + 18, x + 178, y + 4)
    pdf.saveState()
    pdf.setLineWidth(2.5)
    pdf.setStrokeColor(_hex(theme["secondary"]))
    pdf.drawPath(path, fill=0, stroke=1)
    pdf.setLineWidth(1)
    pdf.line(x, y - 18, x + width, y - 18)
    pdf.restoreState()


def _draw_verification_seal(pdf, center_x, center_y, theme):
    pdf.saveState()
    pdf.setFillColor(_hex(theme["seal"]))
    pdf.setStrokeColor(_hex(theme["secondary"]))
    pdf.setLineWidth(2)
    pdf.circle(center_x, center_y, 52, fill=1, stroke=1)
    pdf.circle(center_x, center_y, 40, fill=0, stroke=1)
    pdf.setFillColor(_hex(theme["secondary"]))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(center_x, center_y + 8, "VERIFIED")
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(center_x, center_y - 10, "PLMS RECORD")
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(center_x, center_y + 28, "CERTIFICATE")
    pdf.drawCentredString(center_x, center_y - 28, "AUTHENTIC")
    pdf.restoreState()


def _draw_centered_block(pdf, lines, start_y, font_name, font_size, line_gap, color_value):
    pdf.saveState()
    pdf.setFillColor(color_value)
    pdf.setFont(font_name, font_size)
    current_y = start_y
    for line in lines:
        pdf.drawCentredString(pdf._pagesize[0] / 2, current_y, line)
        current_y -= line_gap
    pdf.restoreState()
    return current_y


def generate_certificate_pdf(certificate, issued_at=None):
    presentation = build_certificate_view_model(certificate, issued_at=issued_at)
    if not REPORTLAB_AVAILABLE:
        return _generate_basic_pdf(presentation)

    buffer = BytesIO()
    page_size = landscape(A4)
    width, height = page_size
    pdf = canvas.Canvas(buffer, pagesize=page_size, pageCompression=1)
    theme = presentation["theme"]

    pdf.setTitle(f"{presentation['course_title']} Certificate")
    pdf.setAuthor(presentation["brand_name"])
    pdf.setSubject("Course completion certificate")

    pdf.setFillColor(_hex(theme["surface"]))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)

    _draw_wave(pdf, width, height, theme)
    _draw_circle_pattern(pdf, width, height, theme)
    _draw_body_pattern(pdf)

    _draw_hex_badge(pdf, 92, height - 64, 24, theme, presentation["course_monogram"])

    pdf.saveState()
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(130, height - 55, presentation["brand_name"])
    pdf.setFont("Helvetica", 10)
    pdf.drawString(130, height - 72, presentation["brand_subtitle"])
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 118, presentation["completion_label"].upper())
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(width / 2, height - 140, "Issued after successfully completing a PLMS learning track")
    pdf.restoreState()

    pdf.saveState()
    pdf.setFillColor(_hex(theme["ink"]))
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height * 0.49, "This certifies that")
    pdf.restoreState()

    name_lines = simpleSplit(presentation["learner_name"], "Helvetica-Bold", 28, width - 220)
    last_y = _draw_centered_block(
        pdf,
        name_lines,
        height * 0.43,
        "Helvetica-Bold",
        28,
        32,
        _hex(theme["ink"]),
    )
    last_y = _draw_profile_line(pdf, presentation, last_y - 2, theme)

    pdf.saveState()
    pdf.setFillColor(_hex(theme["muted"]))
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(width / 2, last_y - 4, "has successfully completed")
    pdf.restoreState()

    course_lines = simpleSplit(presentation["course_title"], "Helvetica-Bold", 21, width - 260)
    last_y = _draw_centered_block(
        pdf,
        course_lines,
        last_y - 34,
        "Helvetica-Bold",
        21,
        26,
        _hex(theme["secondary"]),
    )

    if presentation["badge_name"]:
        ribbon_width = min(width - 250, max(220, len(presentation["badge_name"]) * 7))
        ribbon_x = (width - ribbon_width) / 2
        ribbon_y = last_y - 18
        pdf.saveState()
        pdf.setFillColor(_hex(theme["secondary"]))
        pdf.roundRect(ribbon_x, ribbon_y, ribbon_width, 24, 12, fill=1, stroke=0)
        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawCentredString(width / 2, ribbon_y + 8, f"Completion badge: {presentation['badge_name']}")
        pdf.restoreState()
        pill_y = ribbon_y - 66
    else:
        pill_y = last_y - 72

    metadata_items = [
        ("Completed on", presentation["issued_date"]),
        ("Certificate ID", presentation["certificate_number"]),
    ]
    if presentation["show_profile_fact"]:
        metadata_items.append(
            (presentation["profile_fact_label"], presentation["profile_fact_value"])
        )

    pill_width = 160 if len(metadata_items) >= 3 else 204
    gap = 16 if len(metadata_items) >= 3 else 20
    start_x = (width - ((pill_width * len(metadata_items)) + (gap * (len(metadata_items) - 1)))) / 2
    for index, (label, value) in enumerate(metadata_items):
        x = start_x + (index * (pill_width + gap))
        _draw_metadata_pill(pdf, x, pill_y, pill_width, label, value, theme)

    signature_x = 86
    signature_y = 92
    _draw_signature(pdf, signature_x, signature_y, 190, theme)
    pdf.saveState()
    pdf.setFillColor(_hex(theme["ink"]))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(signature_x, 56, presentation["signatory_name"])
    pdf.setFont("Helvetica", 10)
    pdf.drawString(signature_x, 41, presentation["signatory_title"])
    pdf.restoreState()

    _draw_verification_seal(pdf, width - 102, 138, theme)

    pdf.saveState()
    pdf.setFillColor(_hex(theme["muted"]))
    pdf.setFont("Helvetica", 9)
    pdf.drawString(width - 310, 54, presentation["verification_copy"])
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(width - 310, 39, f"Track: {presentation['course_track']}")
    pdf.restoreState()

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
