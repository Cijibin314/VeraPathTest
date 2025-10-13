from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='analytics_dashboard'),
    path('specialties/', views.specialty_dashboard, name='specialty_dashboard'),
    path('providers/', views.provider_list, name='provider_list'),
    path('referrals/new/', views.create_referral, name='create_referral'),
    path('referrals/<int:pk>/', views.referral_detail, name='referral_detail'),
    path('referrals/<int:pk>/status/<str:state>/', views.set_referral_status, name='set_referral_status'),
    path('referrals/<int:pk>/delete/', views.delete_referral, name='delete_referral'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('metrics/<str:metric>/', views.metric_detail, name='metric_detail'),
    path('specialties/<str:specialty>/', views.specialty_detail, name='specialty_detail'),

]
