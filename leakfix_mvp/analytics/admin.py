from django.contrib import admin
from .models import Payer, Provider, Patient, Referral, Metric, ReferralHistory

@admin.register(Payer)
class PayerAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ('npi', 'full_name', 'specialty', 'city', 'state')
    search_fields = ('npi', 'full_name', 'specialty', 'city', 'state')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('pseudonym',)
    search_fields = ('pseudonym',)

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('patient', 'provider', 'payer', 'status', 'in_network', 'cost_value', 'referral_date')
    list_filter = ('status', 'in_network', 'payer')
    search_fields = ('patient__pseudonym', 'provider__full_name', 'payer__name')

@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'computed_at')
    search_fields = ('name',)

@admin.register(ReferralHistory)
class ReferralHistoryAdmin(admin.ModelAdmin):
    list_display = ('referral', 'status', 'at')
    list_filter = ('status',)
    search_fields = ('referral__id',)

