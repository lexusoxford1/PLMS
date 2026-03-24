import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from django.conf import settings


logger = logging.getLogger(__name__)

PREVIEW_ROOT_NAME = "presentation_previews"
SLIDE_EXPORT_WIDTH = 1920
SLIDE_EXPORT_HEIGHT = 1080
EXPORT_TIMEOUT_SECONDS = 30
SUPPORTED_PRESENTATION_EXTENSIONS = {".ppt", ".pptx"}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def ensure_presentation_preview(material):
    if not getattr(material, "pk", None):
        return {}

    extension = (getattr(material, "file_extension", "") or "").lower()
    if extension not in SUPPORTED_PRESENTATION_EXTENSIONS:
        return {}

    source_path = get_local_material_path(material)
    if not source_path or not source_path.exists():
        return {}

    preview_directory = get_preview_directory(material)
    manifest_path = preview_directory / "manifest.json"
    source_signature = build_source_signature(source_path)
    existing_manifest = load_manifest(manifest_path)

    if existing_manifest and existing_manifest.get("source_signature") == source_signature:
        payload = build_preview_payload(preview_directory, existing_manifest)
        if payload.get("available") or existing_manifest.get("status") == "error":
            return payload

    preview_directory.parent.mkdir(parents=True, exist_ok=True)
    clear_preview_directory(preview_directory)
    preview_directory.mkdir(parents=True, exist_ok=True)

    manifest = {
        "status": "error",
        "kind": "unavailable",
        "source_signature": source_signature,
        "slides": [],
        "slide_count": 0,
        "pdf_name": "",
        "error": "Preview generation was unavailable in the current environment.",
    }

    try:
        result = export_presentation_assets(
            source_path=source_path,
            slides_directory=preview_directory / "slides",
            pdf_path=preview_directory / "preview.pdf",
        )
        slide_names = collect_slide_file_names(preview_directory / "slides")
        pdf_path = preview_directory / "preview.pdf"

        if slide_names:
            manifest.update(
                {
                    "status": "ready",
                    "kind": "slide_images",
                    "slides": slide_names,
                    "slide_count": len(slide_names),
                    "pdf_name": pdf_path.name if pdf_path.exists() else "",
                    "error": result.get("warning", ""),
                }
            )
        elif pdf_path.exists():
            manifest.update(
                {
                    "status": "ready",
                    "kind": "pdf",
                    "slides": [],
                    "slide_count": 0,
                    "pdf_name": pdf_path.name,
                    "error": result.get("warning", ""),
                }
            )
        else:
            manifest["error"] = result.get("error") or manifest["error"]
    except Exception:
        logger.exception(
            "Presentation preview generation failed for learning material %s.",
            material.pk,
        )

    save_manifest(manifest_path, manifest)
    return build_preview_payload(preview_directory, manifest)


def get_local_material_path(material):
    file_field = getattr(material, "file", None)
    if not file_field:
        return None
    try:
        file_path = Path(file_field.path)
    except (AttributeError, NotImplementedError, ValueError):
        return None
    return file_path


def get_preview_directory(material):
    return Path(settings.MEDIA_ROOT) / PREVIEW_ROOT_NAME / str(material.pk)


def build_source_signature(source_path):
    stats = source_path.stat()
    return f"{source_path.name}:{stats.st_size}:{stats.st_mtime_ns}"


def load_manifest(manifest_path):
    if not manifest_path.exists():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_manifest(manifest_path, manifest):
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def clear_preview_directory(preview_directory):
    if preview_directory.exists():
        shutil.rmtree(preview_directory, ignore_errors=True)


def build_preview_payload(preview_directory, manifest):
    slides_directory = preview_directory / "slides"
    slides = []
    for index, file_name in enumerate(manifest.get("slides") or [], start=1):
        file_path = slides_directory / file_name
        if not file_path.exists():
            continue
        image_url = media_url_for_path(file_path)
        slides.append(
            {
                "index": index,
                "label": f"Slide {index}",
                "image_url": image_url,
                "thumb_url": image_url,
            }
        )

    pdf_url = ""
    pdf_name = manifest.get("pdf_name") or ""
    if pdf_name:
        pdf_path = preview_directory / pdf_name
        if pdf_path.exists():
            pdf_url = media_url_for_path(pdf_path)

    available = bool(slides or pdf_url)
    kind = manifest.get("kind") or ("slide_images" if slides else "pdf" if pdf_url else "unavailable")

    return {
        "status": manifest.get("status") or ("ready" if available else "error"),
        "kind": kind,
        "available": available,
        "slides": slides,
        "slide_count": len(slides),
        "cover_url": slides[0]["image_url"] if slides else "",
        "pdf_url": pdf_url,
        "error": manifest.get("error", ""),
    }


def export_presentation_assets(source_path, slides_directory, pdf_path):
    if not sys.platform.startswith("win"):
        return {"error": "Local slide rendering currently requires a supported Windows presentation export tool."}

    if not powerpoint_exists():
        return {"error": "Microsoft PowerPoint was not found for local slide export."}

    slides_directory.mkdir(parents=True, exist_ok=True)
    return export_with_powerpoint(source_path, slides_directory, pdf_path)


def powerpoint_exists():
    if shutil.which("POWERPNT.EXE"):
        return True

    candidate_roots = [
        os.environ.get("ProgramFiles", ""),
        os.environ.get("ProgramFiles(x86)", ""),
    ]
    candidate_paths = []
    for root in candidate_roots:
        if not root:
            continue
        base_root = Path(root)
        candidate_paths.extend(
            [
                base_root / "Microsoft Office" / "root" / "Office16" / "POWERPNT.EXE",
                base_root / "Microsoft Office" / "Office16" / "POWERPNT.EXE",
                base_root / "Microsoft Office" / "root" / "Office15" / "POWERPNT.EXE",
                base_root / "Microsoft Office" / "Office15" / "POWERPNT.EXE",
            ]
        )
    return any(path.exists() for path in candidate_paths)


def export_with_powerpoint(source_path, slides_directory, pdf_path):
    command = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        build_powerpoint_export_script(source_path, slides_directory, pdf_path),
    ]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=EXPORT_TIMEOUT_SECONDS,
        check=False,
    )
    if result.returncode != 0:
        error_output = (result.stderr or result.stdout or "").strip()
        logger.warning("PowerPoint slide export failed: %s", error_output)
        return {
            "error": error_output or "PowerPoint could not export the presentation preview in this session.",
        }
    return {}


def build_powerpoint_export_script(source_path, slides_directory, pdf_path):
    source_literal = powershell_literal(source_path)
    slides_literal = powershell_literal(slides_directory)
    pdf_literal = powershell_literal(pdf_path)
    return f"""
$ErrorActionPreference = 'Stop'
$sourcePath = {source_literal}
$slidesPath = {slides_literal}
$pdfPath = {pdf_literal}
$powerpoint = $null
$presentation = $null

try {{
    New-Item -ItemType Directory -Path $slidesPath -Force | Out-Null
    $powerpoint = New-Object -ComObject PowerPoint.Application
    $presentation = $powerpoint.Presentations.Open($sourcePath, -1, 0, 0)
    $presentation.Export($slidesPath, 'PNG', {SLIDE_EXPORT_WIDTH}, {SLIDE_EXPORT_HEIGHT})
    try {{
        $presentation.SaveAs($pdfPath, 32)
    }} catch {{
    }}
}} finally {{
    if ($presentation -ne $null) {{
        $presentation.Close()
    }}
    if ($powerpoint -ne $null) {{
        $powerpoint.Quit()
    }}
}}
""".strip()


def powershell_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def collect_slide_file_names(slides_directory):
    if not slides_directory.exists():
        return []
    slide_paths = [
        path.name
        for path in slides_directory.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    ]
    return sorted(slide_paths, key=natural_sort_key)


def natural_sort_key(value):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", str(value))]


def media_url_for_path(file_path):
    relative_path = Path(file_path).resolve().relative_to(Path(settings.MEDIA_ROOT).resolve())
    return f"{settings.MEDIA_URL}{relative_path.as_posix()}"
