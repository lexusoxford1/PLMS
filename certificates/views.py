import os

from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render

from LMS.utils import course_completion_percentage
from courses.models import Enrollment

from .models import Certificate
from .presentation import build_certificate_view_model, build_certificate_preview_model, build_default_certificate_preview


@login_required
def certificate_list(request):
    certificates = list(
        Certificate.objects.filter(user=request.user)
        .select_related("user", "course", "course__created_by", "badge")
        .order_by("-issued_at", "-created_at")
    )
    earned_course_ids = {certificate.course_id for certificate in certificates}
    certificate_cards = [
        {
            "certificate": certificate,
            "course": certificate.course,
            "presentation": build_certificate_view_model(certificate),
            "progress_percent": 100,
        }
        for certificate in certificates
    ]
    preview_cards = [
        {
            "course": enrollment.course,
            "presentation": build_certificate_preview_model(enrollment.course, request.user),
            "progress_percent": course_completion_percentage(request.user, enrollment.course),
        }
        for enrollment in Enrollment.objects.filter(user=request.user)
        .select_related("course", "course__created_by")
        .order_by("-enrolled_at")
        if enrollment.course_id not in earned_course_ids
    ]
    return render(
        request,
        "certificates/certificate_list.html",
        {
            "certificate_cards": certificate_cards,
            "preview_cards": preview_cards,
            "certificate_count": len(certificate_cards),
            "preview_count": len(preview_cards),
            "latest_certificate": certificate_cards[0] if certificate_cards else None,
            "default_preview": build_default_certificate_preview(),
        },
    )


@login_required
def certificate_detail(request, pk):
    certificate = get_object_or_404(
        Certificate.objects.select_related("user", "course", "course__created_by", "badge"),
        pk=pk,
        user=request.user,
    )
    certificate.refresh_artifact()
    presentation = build_certificate_view_model(certificate)
    return render(
        request,
        "certificates/certificate_view.html",
        {
            "certificate": certificate,
            "presentation": presentation,
        },
    )


@login_required
def certificate_download(request, pk):
    certificate = get_object_or_404(
        Certificate.objects.select_related("user", "course", "course__created_by", "badge"),
        pk=pk,
        user=request.user,
    )
    certificate.refresh_artifact()
    certificate.file.open("rb")
    return FileResponse(
        certificate.file,
        as_attachment=True,
        filename=os.path.basename(certificate.file.name),
    )
