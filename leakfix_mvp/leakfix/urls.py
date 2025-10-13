"""
URL configuration for leakfix project.

Routes requests to views.  The `urlpatterns` list routes URLs to views.
We include paths for the Django admin, the analytics app, and a simple
redirect from the root URL to our dashboard.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Redirect root to dashboard view in analytics
    path('', RedirectView.as_view(url='/dashboard/')),
    # Include analytics URLs for metrics and dashboard
    path('', include('analytics.urls')),
]
