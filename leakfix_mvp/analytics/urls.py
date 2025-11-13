from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='analytics_dashboard'),
    path('specialties/', views.specialty_dashboard, name='specialty_dashboard'),
    path('providers/', views.provider_list, name='provider_list'),
    path('providers/search/', views.provider_search, name='provider_search'),
    path('referrals/new/', views.create_referral, name='create_referral'),
    path('referrals/<int:pk>/', views.referral_detail, name='referral_detail'),
    path('referrals/<int:pk>/status/<str:state>/', views.set_referral_status, name='set_referral_status'),
    path('referrals/<int:pk>/delete/', views.delete_referral, name='delete_referral'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('metrics/<str:metric>/', views.metric_detail, name='metric_detail'),
    path('specialties/<str:specialty>/', views.specialty_detail, name='specialty_detail'),
    path('find-slots/', views.find_provider_slots, name='find_provider_slots'),
    path('provider-details/<int:providerid>/', views.get_provider_details_ajax, name='get_provider_details_ajax'),
    path('sorted-providers/', views.get_sorted_providers_ajax, name='get_sorted_providers_ajax'),
    path('appointment-reasons/', views.get_appointment_reasons_ajax, name='get_appointment_reasons_ajax'),
    path('provider-departments/<int:providerid>/', views.get_provider_departments_ajax, name='get_provider_departments_ajax'),
    path('provider-departments/', views.get_provider_departments_ajax, name='get_all_departments_ajax'),
    path('create-referral-order/', views.create_referral_order_ajax, name='create_referral_order_ajax'),
    path('search-appointment-reasons/', views.search_appointment_reasons_ajax, name='search_appointment_reasons_ajax'),
    path('patient-search/', views.patient_search_ajax, name='patient_search_ajax'),
    path('patient-insurances/<str:patient_id>/', views.get_patient_insurances_ajax, name='get_patient_insurances_ajax'),
    path('management/', views.management, name='management'),
    path('management/stream-command/', views.stream_command_view, name='stream_command_view'),
    path('management/sync-stream/', views.sync_stream_view, name='sync_stream_view'),

]
