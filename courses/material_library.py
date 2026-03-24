from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .presentation_previews import ensure_presentation_preview


def merge_query_string(url, **params):
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    for key, value in params.items():
        if value is None:
            continue
        query[str(key)] = str(value)
    return urlunparse(parsed._replace(query=urlencode(query)))


def normalize_google_slides_embed_url(url):
    value = str(url or "").strip()
    if not value:
        return ""

    parsed = urlparse(value)
    path = parsed.path.rstrip("/")
    for suffix in ("/edit", "/present", "/preview", "/pub"):
        if path.endswith(suffix):
            path = f"{path[: -len(suffix)]}/embed"
            break
    if not path.endswith("/embed"):
        path = f"{path}/embed"

    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("rm", "minimal")
    return urlunparse(parsed._replace(path=path, query=urlencode(query)))


def normalize_canva_embed_url(url):
    value = str(url or "").strip()
    if not value:
        return ""
    return merge_query_string(value, embed=1)


def build_material_embed_url(material, request=None):
    source_url = material.source_url
    if not source_url:
        return ""

    if material.is_presentation:
        if material.presentation_provider == material.PRESENTATION_PROVIDER_GOOGLE_SLIDES:
            return normalize_google_slides_embed_url(source_url)
        if material.presentation_provider == material.PRESENTATION_PROVIDER_CANVA:
            return normalize_canva_embed_url(source_url)
        if material.presentation_provider == material.PRESENTATION_PROVIDER_EMBED:
            return source_url
        if material.presentation_provider == material.PRESENTATION_PROVIDER_UPLOAD:
            if material.file_extension == ".pdf":
                return source_url
            return ""

    if material.material_type == material.MATERIAL_IMAGE:
        return source_url
    if material.file_extension == ".pdf":
        return source_url
    return ""


def build_material_view_model(material, request=None, ensure_preview_assets=False):
    source_url = material.source_url
    embed_url = build_material_embed_url(material, request=request)
    preview = {}
    if (
        ensure_preview_assets
        and material.presentation_provider == material.PRESENTATION_PROVIDER_UPLOAD
        and material.file_extension in {".ppt", ".pptx"}
    ):
        preview = ensure_presentation_preview(material)

    if not embed_url and preview.get("pdf_url"):
        embed_url = preview.get("pdf_url")

    if preview.get("kind") == "slide_images" and preview.get("slides"):
        viewer_kind = "slides"
    elif material.material_type == material.MATERIAL_IMAGE:
        viewer_kind = "image"
    elif embed_url:
        viewer_kind = "iframe"
    else:
        viewer_kind = "download"

    return {
        "id": material.id,
        "title": material.title,
        "description": material.description,
        "material_type": material.material_type,
        "material_type_label": material.get_material_type_display(),
        "source_type": material.source_type,
        "source_type_label": material.get_source_type_display(),
        "presentation_provider": material.presentation_provider,
        "presentation_provider_label": material.get_presentation_provider_display(),
        "order": material.order,
        "source_url": source_url,
        "embed_url": embed_url,
        "file_name": material.file_name,
        "file_extension": material.file_extension,
        "is_presentation": material.is_presentation,
        "viewer_kind": viewer_kind,
        "supports_embed": viewer_kind in {"slides", "iframe", "image"},
        "preview_status": preview.get("status", ""),
        "preview_kind": preview.get("kind", ""),
        "preview_error": preview.get("error", ""),
        "preview_slides": preview.get("slides", []),
        "preview_slide_count": preview.get("slide_count", 0),
        "preview_cover_url": preview.get("cover_url", ""),
        "preview_pdf_url": preview.get("pdf_url", ""),
        "viewer_mode_label": build_material_viewer_mode_label(material, viewer_kind),
        "primary_action_label": build_material_primary_action_label(material),
        "secondary_action_url": build_material_secondary_action_url(material, preview),
        "secondary_action_label": build_material_secondary_action_label(material, preview),
        "viewer_note": build_material_viewer_note(material, embed_url, preview=preview),
    }


def build_material_viewer_note(material, embed_url, preview=None):
    preview = preview or {}
    if not material.is_presentation:
        return ""
    if material.presentation_provider == material.PRESENTATION_PROVIDER_UPLOAD and material.file_extension in {".ppt", ".pptx"}:
        if preview.get("slides"):
            return "Rendered as slide images for a more stable, lecture-friendly viewer."
        if preview.get("pdf_url"):
            return "A generated PDF preview is available when direct slide images are not ready."
        if preview.get("error"):
            return "This uploaded deck could not be rendered into preview slides in the current environment. Open or download the source file."
        return "This uploaded deck will use generated preview slides when local presentation export is available."
    if material.presentation_provider == material.PRESENTATION_PROVIDER_UPLOAD and material.file_extension == ".pdf":
        return "This uploaded PDF deck opens in the lesson viewer with your browser's document renderer."
    if material.presentation_provider == material.PRESENTATION_PROVIDER_GOOGLE_SLIDES:
        return "Google Slides content is shown in the lecture viewer when the link is accessible."
    if material.presentation_provider == material.PRESENTATION_PROVIDER_CANVA:
        return "Canva presentations open in the lecture viewer when the shared design supports embedding."
    if material.presentation_provider == material.PRESENTATION_PROVIDER_EMBED:
        return "This presentation uses the provided embed link."
    return ""


def build_material_viewer_mode_label(material, viewer_kind):
    if viewer_kind == "slides":
        return "Slide preview"
    if viewer_kind == "iframe" and material.presentation_provider == material.PRESENTATION_PROVIDER_UPLOAD and material.file_extension in {".ppt", ".pptx"}:
        return "PDF preview"
    if viewer_kind == "iframe" and material.file_extension == ".pdf":
        return "PDF viewer"
    if viewer_kind == "iframe":
        return "Embedded deck"
    if viewer_kind == "image":
        return "Image preview"
    if material.presentation_provider == material.PRESENTATION_PROVIDER_UPLOAD:
        return "Open file"
    return "Open source"


def build_material_primary_action_label(material):
    if material.source_type == material.SOURCE_FILE:
        return "Download deck" if material.is_presentation else "Download file"
    return "Open source"


def build_material_secondary_action_url(material, preview):
    pdf_url = (preview or {}).get("pdf_url") or ""
    if material.presentation_provider == material.PRESENTATION_PROVIDER_UPLOAD and pdf_url and pdf_url != material.source_url:
        return pdf_url
    return ""


def build_material_secondary_action_label(material, preview):
    if build_material_secondary_action_url(material, preview):
        return "Open PDF preview"
    return ""


def build_flat_presentation_slide(item, preview_slide):
    slide_index = int(preview_slide.get("index") or 0)
    slide_label = preview_slide.get("label") or f"Slide {slide_index or 1}"
    deck_title = item.get("title") or "Lecture presentation"
    file_name = item.get("file_name") or ""
    alt_parts = [deck_title, slide_label]
    if file_name:
        alt_parts.append(file_name)
    return {
        "id": f"{item['id']}-{slide_index or 1}",
        "deck_id": item["id"],
        "deck_order": item["order"],
        "deck_title": deck_title,
        "file_name": file_name,
        "slide_index": slide_index or 1,
        "slide_label": slide_label,
        "image_url": preview_slide.get("image_url", ""),
        "pdf_url": item.get("secondary_action_url", ""),
        "pdf_label": item.get("secondary_action_label", ""),
        "download_url": item.get("source_url", ""),
        "download_label": item.get("primary_action_label", ""),
        "alt": " - ".join(part for part in alt_parts if part),
    }


def build_presentation_viewer(presentations):
    slides = []
    slide_renderable_ids = set()

    for item in presentations:
        if item.get("viewer_kind") != "slides" or not item.get("preview_slides"):
            continue

        slide_renderable_ids.add(item["id"])
        for preview_slide in item["preview_slides"]:
            slides.append(build_flat_presentation_slide(item, preview_slide))

    if not slides:
        return {
            "enabled": False,
            "slides": [],
            "total_slides": 0,
            "initial_slide": {},
            "slide_renderable_ids": slide_renderable_ids,
        }

    return {
        "enabled": True,
        "slides": slides,
        "total_slides": len(slides),
        "initial_slide": slides[0],
        "slide_renderable_ids": slide_renderable_ids,
    }


def build_supplemental_resources(materials, slide_renderable_ids):
    resources = []
    for item in materials:
        if item["is_presentation"] and item["id"] in slide_renderable_ids:
            continue
        resources.append(item)
    return resources


def build_lesson_material_collections(lesson, request=None):
    materials = [
        build_material_view_model(material, request=request, ensure_preview_assets=True)
        for material in lesson.materials.all()
    ]
    presentations = [item for item in materials if item["is_presentation"]]
    attachments = [item for item in materials if not item["is_presentation"]]
    presentation_viewer = build_presentation_viewer(presentations)
    supplemental_resources = build_supplemental_resources(
        materials,
        presentation_viewer["slide_renderable_ids"],
    )
    return {
        "materials": materials,
        "presentations": presentations,
        "attachments": attachments,
        "presentation_viewer": presentation_viewer,
        "supplemental_resources": supplemental_resources,
    }
