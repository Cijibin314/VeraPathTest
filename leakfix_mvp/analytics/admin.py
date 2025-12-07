from django.contrib import admin
from .models import Payer, Provider, Patient, Referral, Metric, ReferralHistory, Practice, UserProfile, CPTCodeMapping

class ProviderInline(admin.TabularInline):
    model = Provider
    extra = 0  # Don't show extra empty forms
    fields = ('full_name', 'specialty', 'is_in_network')
    readonly_fields = ('full_name', 'specialty')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Payer)
class PayerAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Practice)
class PracticeAdmin(admin.ModelAdmin):
    list_display = ('name', 'athena_practice_id', 'location')
    search_fields = ('name', 'athena_practice_id', 'location')
    inlines = [ProviderInline]

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'practice')
    list_filter = ('practice',)
    search_fields = ('user__username', 'practice__name')

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
    list_display = ('patient', 'provider', 'payer', 'status', 'in_network', 'rvu_cost', 'referral_date')
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

@admin.register(CPTCodeMapping)
class CPTCodeMappingAdmin(admin.ModelAdmin):
    list_display = ('ordertypeid', 'name', 'cpt_code', 'work_rvu', 'non_fac_pe_rvu', 'fac_pe_rvu', 'mp_rvu')
    search_fields = ('name', 'cpt_code')

