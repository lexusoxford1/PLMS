from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import UserBadge


@login_required
def badge_list(request):
    badges = UserBadge.objects.filter(user=request.user).select_related("badge", "course")
    return render(request, "badges/badge_list.html", {"badges": badges})
