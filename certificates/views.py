import os

from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render

from .models import Certificate


@login_required
def certificate_list(request):
    certificates = Certificate.objects.filter(user=request.user).select_related("course", "badge")
    return render(request, "certificates/certificate_list.html", {"certificates": certificates})


@login_required
def certificate_detail(request, pk):
    certificate = get_object_or_404(Certificate.objects.select_related("course", "badge"), pk=pk, user=request.user)
    return render(request, "certificates/certificate_view.html", {"certificate": certificate})


@login_required
def certificate_download(request, pk):
    certificate = get_object_or_404(Certificate, pk=pk, user=request.user)
    if not certificate.file:
        certificate.issue(send_email=False)
    certificate.file.open("rb")
    return FileResponse(
        certificate.file,
        as_attachment=True,
        filename=os.path.basename(certificate.file.name),
    )
