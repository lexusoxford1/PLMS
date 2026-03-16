from django.urls import path

from .views import quiz_detail


urlpatterns = [
    path("<int:quiz_id>/", quiz_detail, name="quiz_detail"),
]
