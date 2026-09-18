"""Ad routes (mounted under /ads/)."""
from django.urls import path

from .views import ad_click

urlpatterns = [
    path("click/<uuid:impression_id>/", ad_click, name="ad-click"),
]
