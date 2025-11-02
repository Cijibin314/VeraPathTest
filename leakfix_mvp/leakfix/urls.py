"""
URL configuration for leakfix project.

Routes requests to views.  The `urlpatterns` list routes URLs to views.
We include paths for the Django admin, the analytics app, and a simple
redirect from the root URL to our dashboard.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # Redirect root to dashboard view in analytics
    path('', RedirectView.as_view(url='/dashboard/')),
    # Include analytics URLs for metrics and dashboard
    path('', include('analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
