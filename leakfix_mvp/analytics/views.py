from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Avg
from django.utils import timezone
from statistics import median
from datetime import timedelta
from .models import (
    Referral,
    Provider,
    Patient,
    Payer,
    ReferralHistory,
    Invoice,
    UserProfile,
    Practice,
)
from .forms import ReferralForm
from analytics.ai_utils import generate_suggestions
import logging

# --- KPI dashboard ---
@login_required
def dashboard(request):
    debug_message = ""
    try:
        user_practice = request.user.userprofile.practice
        if user_practice:
            debug_message = f"Filtering referrals for practice: '{user_practice.name}' (Athena ID: {user_practice.athena_practice_id}). "
            
            total_referrals_in_db = Referral.objects.count()
            providers_in_practice = Provider.objects.filter(practice=user_practice).count()
            referrals_for_practice = Referral.objects.filter(provider__practice=user_practice)
            
            debug_message += f"Found {total_referrals_in_db} total referrals in DB. "
            debug_message += f"Found {providers_in_practice} providers in this practice. "
            debug_message += f"The dashboard query for this practice found {referrals_for_practice.count()} referrals."

            referrals = referrals_for_practice
        else:
            user_practice = None # Ensure it's None if no practice is found
            debug_message = "User is not associated with a practice. Showing all referrals."
            referrals = Referral.objects.all()
    except (UserProfile.DoesNotExist, AttributeError):
        user_practice = None
        debug_message = "User has no UserProfile or it's incomplete. Showing all referrals."
        referrals = Referral.objects.all()

    total = referrals.count()
    in_network = referrals.filter(in_network=True).count()
    out_network = referrals.filter(in_network=False).count()
    leakage_cost = (
        referrals.filter(in_network=False).aggregate(total_leak=Sum('cost_value')).get('total_leak')
        or 0
    )
    # New: average leakage cost across all referrals
    avg_leakage_cost = (leakage_cost / out_network) if out_network else 0

    durations_completion = [
        (ref.completed_at.date() - ref.referral_date).days
        for ref in referrals.filter(completed_at__isnull=False)
    ]
    median_days_completion = median(durations_completion) if durations_completion else 0

    durations_ack = [
        (ref.ack_at.date() - ref.referral_date).days
        for ref in referrals.filter(ack_at__isnull=False)
    ]
    median_days_ack = median(durations_ack) if durations_ack else 0

    durations_sched = [
        (ref.scheduled_at.date() - ref.referral_date).days
        for ref in referrals.filter(scheduled_at__isnull=False)
    ]
    median_days_schedule = median(durations_sched) if durations_sched else 0

    attempts = [ref.history.count() for ref in referrals.filter(scheduled_at__isnull=False)]
    avg_attempts = (sum(attempts) / len(attempts)) if attempts else 0

    in_network_rate = (in_network / total * 100.0) if total else 0
    completed = referrals.filter(status=Referral.Status.COMPLETED).count()
    completion_rate = (completed / total * 100.0) if total else 0

    top_leakage = (
        referrals.filter(in_network=False)
        .values('provider__full_name')
        .annotate(total_leak=Sum('cost_value'))
        .order_by('-total_leak')[:5]
    )

    top_payer_leakage = (
        referrals.filter(in_network=False, payer__isnull=False)
        .values('payer__name')
        .annotate(total_leak=Sum('cost_value'))
        .order_by('-total_leak')[:5]
    )

    avg_in_cost = referrals.filter(in_network=True).aggregate(avg=Avg('cost_value'))['avg'] or 0
    retained_revenue = in_network * avg_in_cost

    context = {
        'total': total,
        'in_network': in_network,
        'out_network': out_network,
        'in_network_rate': in_network_rate,
        'completion_rate': completion_rate,
        'leakage_cost': leakage_cost,
        'avg_leakage_cost': avg_leakage_cost,
        'retained_revenue': retained_revenue,
        'median_days_completion': median_days_completion,
        'median_days_ack': median_days_ack,
        'median_days_schedule': median_days_schedule,
        'avg_attempts': avg_attempts,
        'top_leakage': list(top_leakage),
        'top_payer_leakage': list(top_payer_leakage),
        'debug_message': debug_message,
    }
    return render(request, 'analytics/dashboard.html', context)


import json
import os
from django.conf import settings
from django.http import JsonResponse

from django.db.models.functions import Coalesce

# --- Provider list ---
@login_required
def provider_list(request):
    try:
        user_practice = request.user.userprofile.practice
    except (UserProfile.DoesNotExist, AttributeError):
        user_practice = None

    if user_practice:
        providers = list(Provider.objects.filter(practice=user_practice))
    else:
        providers = list(Provider.objects.all())

    for provider in providers:
        score = 0
        # Completeness score calculation (existing logic)
        if provider.full_name: score += 1
        if provider.specialty: score += 1
        if provider.subspecialty: score += 1
        if provider.city: score += 1
        if provider.state: score += 1
        if provider.npi: score += 1
        if provider.accepting_new_patients is not None: score += 1
        if provider.primary_department: score += 1
        provider.completeness_score = score

        # Use the is_in_network field from the model
        provider.is_preferred = provider.is_in_network

    # Sort: preferred (in-network) providers first, then by completeness score
    providers.sort(key=lambda p: (p.is_preferred, p.completeness_score), reverse=True)

    return render(request, 'analytics/provider_list.html', {'providers': providers})


# --- Provider search ---
@login_required
def provider_search(request):
    query = request.GET.get('q', '').strip()

    try:
        user_practice = request.user.userprofile.practice
    except (UserProfile.DoesNotExist, AttributeError):
        user_practice = None

    if user_practice:
        providers = Provider.objects.filter(practice=user_practice)
    else:
        providers = Provider.objects.all()

    if query:
        providers = providers.filter(
            Q(full_name__icontains=query)
            | Q(specialty__icontains=query)
            | Q(city__icontains=query)
            | Q(state__icontains=query)
            | Q(primary_department__icontains=query)
        )

    # Calculate completeness_score for each provider object
    for provider in providers:
        score = 0
        # Completeness score calculation
        if provider.full_name: score += 1
        if provider.specialty: score += 1
        if provider.city: score += 1
        if provider.state: score += 1
        if provider.npi: score += 1
        if provider.accepting_new_patients is not None: score += 1
        if provider.primary_department: score += 1
        provider.completeness_score = score

        # Use the is_in_network field from the model
        provider.is_preferred = provider.is_in_network

    # Sort: preferred (in-network) providers first, then by completeness score
    providers = list(providers) # Convert queryset to list for sorting
    providers.sort(key=lambda p: (p.is_preferred, p.completeness_score), reverse=True)

    # Convert Provider objects to dictionaries for JSON response
    data = []
    for provider in providers:
        data.append({
            'full_name': provider.full_name,
            'specialty': provider.specialty,
            'primary_department': provider.primary_department,
            'location': f"{provider.city}, {provider.state}" if provider.city and provider.state else '',
            'npi': provider.npi,
            'providerid': provider.providerid,
            'accepting_new_patients': provider.accepting_new_patients,
            'is_preferred': provider.is_preferred,
            'completeness_score': provider.completeness_score,
        })

    return JsonResponse(data, safe=False)


# --- Suggestion engine helpers (unchanged) ---
def get_provider_metrics():
    metrics = {}
    for provider in Provider.objects.all():
        refs = Referral.objects.filter(provider=provider)
        total = refs.count()
        if total == 0:
            continue
        in_net = refs.filter(in_network=True).count()
        completed = refs.filter(status=Referral.Status.COMPLETED).count()
        durations = [
            (r.completed_at - r.created_at).days
            for r in refs.filter(completed_at__isnull=False)
        ]
        avg_days = (sum(durations) / len(durations)) if durations else 0
        metrics[provider.id] = {
            'in_network_rate': in_net / total,
            'completion_rate': completed / total,
            'avg_days': avg_days,
        }
    return metrics


def get_suggested_providers(referral, max_results=3):
    candidates = Provider.objects.filter(
        specialty__iexact=referral.provider.specialty
    ).exclude(id=referral.provider.id)
    metrics = get_provider_metrics()
    scored = []
    for p in candidates:
        m = metrics.get(p.id, None)
        if m:
            score = (
                0.5 * m['in_network_rate']
                + 0.3 * m['completion_rate']
                - 0.2 * (m['avg_days'] / 30.0)
            )
        else:
            score = 0
        scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:max_results]]


# --- Referral creation & detail views ---
@login_required
def create_referral(request):
    if request.method == 'POST':
        form = ReferralForm(request.POST)
        if form.is_valid():
            provider = form.cleaned_data['provider']
            # The in_network status is now determined by the provider's own flag
            is_in_network = provider.is_in_network

            patient_id = form.cleaned_data['patient_id']
            patient, _ = Patient.objects.get_or_create(original_id=patient_id)
            payer_code = form.cleaned_data.get('payer_code')
            payer = None
            if payer_code:
                payer, _ = Payer.objects.get_or_create(code=payer_code, defaults={'name': payer_code})
            
            referral = Referral.objects.create(
                patient=patient,
                provider=provider,
                payer=payer,
                specialty=form.cleaned_data.get('specialty') or provider.specialty or '',
                in_network=is_in_network, # Set automatically from provider
                is_urgent=form.cleaned_data.get('is_urgent', False),
                suggested_provider_ids=""
            )
            referral.suggested_provider_ids = ','.join(
                str(p.id) for p in get_suggested_providers(referral)
            )
            referral.save()
            ReferralHistory.objects.create(referral=referral, status=referral.status)
            return redirect('referral_detail', pk=referral.id)
    else:
        form = ReferralForm()
    return render(request, 'analytics/create_referral.html', {'form': form})


def referral_detail(request, pk):
    referral = get_object_or_404(Referral, pk=pk)
    suggested = get_suggested_providers(referral)
    metrics = get_provider_metrics()
    suggested_with_metrics = []
    for p in suggested:
        m = metrics.get(p.id, {'in_network_rate': 0, 'completion_rate': 0, 'avg_days': 0})
        suggested_with_metrics.append({'provider': p, 'metrics': m})
    return render(request, 'analytics/referral_detail.html', {
        'referral': referral,
        'suggested_with_metrics': suggested_with_metrics,
    })


def set_referral_status(request, pk, state):
    referral = get_object_or_404(Referral, pk=pk)
    if state in Referral.Status.values:
        now = timezone.now()
        if state == Referral.Status.ACKNOWLEDGED:
            referral.ack_at = now
        elif state == Referral.Status.SCHEDULED:
            referral.scheduled_at = now
        elif state == Referral.Status.COMPLETED:
            referral.completed_at = now
        elif state == Referral.Status.CANCELLED:
            referral.cancelled_at = now
        referral.status = state
        referral.save()
        ReferralHistory.objects.create(referral=referral, status=state)
    return redirect('referral_detail', pk=referral.id)


# --- Invoice views ---
def invoice_list(request):
    invoices = Invoice.objects.order_by('-period_start')
    return render(request, 'analytics/invoice_list.html', {'invoices': invoices})


def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'analytics/invoice_detail.html', {'invoice': invoice})


# --- Metric detail view (unchanged from previous step) ---
def metric_detail(request, metric):
    today = timezone.now().date()
    start_date = (today.replace(day=1) - timedelta(days=365)).replace(day=1)

    # Build a list of month start dates
    months = []
    current = start_date
    while current <= today:
        months.append(current)
        next_month = (current + timedelta(days=32)).replace(day=1)
        current = next_month

    labels = [d.strftime('%b %Y') for d in months]
    values = []

    for month_start in months:
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        month_refs = Referral.objects.filter(created_at__gte=month_start, created_at__lt=month_end)

        if metric == 'in_network_rate':
            total = month_refs.count()
            in_net = month_refs.filter(in_network=True).count()
            value = (in_net / total * 100.0) if total else 0
        elif metric == 'completion_rate':
            total = month_refs.count()
            completed = month_refs.filter(status=Referral.Status.COMPLETED).count()
            value = (completed / total * 100.0) if total else 0
        elif metric == 'leakage_cost':
            value = month_refs.filter(in_network=False).aggregate(total_leak=Sum('cost_value')).get('total_leak') or 0
        elif metric == 'retained_revenue':
            avg_in_cost = month_refs.filter(in_network=True).aggregate(avg=Avg('cost_value'))['avg'] or 0
            in_net_count = month_refs.filter(in_network=True).count()
            value = avg_in_cost * in_net_count
        elif metric == 'referral_volume':
            value = month_refs.count()
        elif metric == 'avg_leakage_cost':
            out_count = month_refs.filter(in_network=False).count()
            total_leak = month_refs.filter(in_network=False).aggregate(total_leak=Sum('cost_value')).get('total_leak') or 0
            value = (total_leak / out_count) if out_count else 0
        else:
            value = 0

        values.append(value)

    # Summary stats
    avg_value = (sum(values) / len(values)) if values else 0
    max_value = max(values) if values else 0
    min_value = min(values) if values else 0
    latest_value = values[-1] if values else 0

    # Simple trend calculation: compare last value to average
    if latest_value > avg_value * 1.05:
        trend = "increasing"
    elif latest_value < avg_value * 0.95:
        trend = "decreasing"
    else:
        trend = "flat"

    # Call the AI suggestion function
    try:
        suggestion_text = generate_suggestions(metric, latest_value, avg_value, trend)
    except Exception as e:
        suggestion_text = f"(AI suggestion unavailable: {e})"

    context = {
        'metric': metric,
        'labels': labels,
        'values': values,
        'avg_value': avg_value,
        'max_value': max_value,
        'min_value': min_value,
        'latest_value': latest_value,
        'trend': trend,
        'suggestion_text': suggestion_text,
    }
    return render(request, 'analytics/metric_detail.html', context)

# --- Specialty dashboard ---
def specialty_dashboard(request):
    """
    Compute metrics for each provider specialty.  This allows clinics
    to compare leakage and completion metrics across specialties.
    """
    specialties = Provider.objects.values_list('specialty', flat=True).distinct()
    specialty_data = []
    for spec in specialties:
        refs = Referral.objects.filter(provider__specialty=spec)
        total = refs.count()
        in_network = refs.filter(in_network=True).count()
        out_network = refs.filter(in_network=False).count()
        leakage_cost = refs.filter(in_network=False).aggregate(total_leak=Sum('cost_value')).get('total_leak') or 0
        avg_leakage_cost = (leakage_cost / out_network) if out_network else 0
        avg_in_cost = refs.filter(in_network=True).aggregate(avg=Avg('cost_value'))['avg'] or 0
        retained_revenue = in_network * avg_in_cost
        durations_completion = [
            (ref.completed_at.date() - ref.referral_date).days
            for ref in refs.filter(completed_at__isnull=False)
        ]
        median_days_completion = median(durations_completion) if durations_completion else 0
        durations_ack = [
            (ref.ack_at.date() - ref.referral_date).days
            for ref in refs.filter(ack_at__isnull=False)
        ]
        median_days_ack = median(durations_ack) if durations_ack else 0
        durations_sched = [
            (ref.scheduled_at.date() - ref.referral_date).days
            for ref in refs.filter(scheduled_at__isnull=False)
        ]
        median_days_schedule = median(durations_sched) if durations_sched else 0
        attempts = [ref.history.count() for ref in refs.filter(scheduled_at__isnull=False)]
        avg_attempts = (sum(attempts) / len(attempts)) if attempts else 0
        in_network_rate = (in_network / total * 100.0) if total else 0
        completed = refs.filter(status=Referral.Status.COMPLETED).count()
        completion_rate = (completed / total * 100.0) if total else 0
        specialty_data.append({
            'specialty': spec,
            'total': total,
            'in_network': in_network,
            'out_network': out_network,
            'in_network_rate': in_network_rate,
            'completion_rate': completion_rate,
            'leakage_cost': leakage_cost,
            'avg_leakage_cost': avg_leakage_cost,
            'retained_revenue': retained_revenue,
            'median_days_completion': median_days_completion,
            'median_days_ack': median_days_ack,
            'median_days_schedule': median_days_schedule,
            'avg_attempts': avg_attempts,
        })
    return render(request, 'analytics/specialty_dashboard.html', {'specialty_data': specialty_data})


def specialty_detail(request, specialty):
    """
    Compute metrics for a single provider specialty.
    """
    refs = Referral.objects.filter(provider__specialty=specialty)
    total = refs.count()
    in_network = refs.filter(in_network=True).count()
    out_network = refs.filter(in_network=False).count()
    leakage_cost = refs.filter(in_network=False).aggregate(total_leak=Sum('cost_value')).get('total_leak') or 0
    avg_leakage_cost = (leakage_cost / out_network) if out_network else 0
    avg_in_cost = refs.filter(in_network=True).aggregate(avg=Avg('cost_value'))['avg'] or 0
    retained_revenue = in_network * avg_in_cost
    durations_completion = [
        (ref.completed_at.date() - ref.referral_date).days
        for ref in refs.filter(completed_at__isnull=False)
    ]
    median_days_completion = median(durations_completion) if durations_completion else 0
    durations_ack = [
        (ref.ack_at.date() - ref.referral_date).days
        for ref in refs.filter(ack_at__isnull=False)
    ]
    median_days_ack = median(durations_ack) if durations_ack else 0
    durations_sched = [
        (ref.scheduled_at.date() - ref.referral_date).days
        for ref in refs.filter(scheduled_at__isnull=False)
    ]
    median_days_schedule = median(durations_sched) if durations_sched else 0
    attempts = [ref.history.count() for ref in refs.filter(scheduled_at__isnull=False)]
    avg_attempts = (sum(attempts) / len(attempts)) if attempts else 0
    in_network_rate = (in_network / total * 100.0) if total else 0
    completed = refs.filter(status=Referral.Status.COMPLETED).count()
    completion_rate = (completed / total * 100.0) if total else 0

    context = {
        'specialty': specialty,
        'total': total,
        'in_network': in_network,
        'out_network': out_network,
        'in_network_rate': in_network_rate,
        'completion_rate': completion_rate,
        'leakage_cost': leakage_cost,
        'avg_leakage_cost': avg_leakage_cost,
        'retained_revenue': retained_revenue,
        'median_days_completion': median_days_completion,
        'median_days_ack': median_days_ack,
        'median_days_schedule': median_days_schedule,
        'avg_attempts': avg_attempts,
    }
    return render(request, 'analytics/specialty_detail.html', context)


from django.http import JsonResponse
import requests
from .athena_client import get_token, get
from datetime import datetime, timedelta
from django.core.cache import cache

@login_required
def find_provider_slots(request):
    provider_id_str = request.GET.get('provider_id')
    reason_id_str = request.GET.get('reasonid')
    search_date_str = request.GET.get('search_date') # New parameter

    if not provider_id_str:
        return JsonResponse({'error': 'provider_id is required'}, status=400)

    try:
        user_practice = request.user.userprofile.practice
        if not user_practice or not user_practice.athena_practice_id:
            return JsonResponse({'error': 'User has no practice ID configured.'}, status=400)
        practice_id = user_practice.athena_practice_id

        provider_id = int(provider_id_str)
        reason_id = int(reason_id_str) if reason_id_str else None

        token = get_token() 
        
        departments_data = get("departments", practice_id, token, params={"limit": 200})
        departments = departments_data.get('departments', [])
        
        all_open_slots = []

        if search_date_str:
            start_date = search_date_str
            end_date = search_date_str
        else:
            start_date = datetime.now().strftime("%m/%d/%Y")
            end_date = (datetime.now() + timedelta(days=90)).strftime("%m/%d/%Y")

        for dept in departments:
            dept_id = int(dept['departmentid'])
            params = {
                    "departmentid": dept_id,
                    "providerid": provider_id,
                    "startdate": start_date,
                    "enddate": end_date,
                }
            if reason_id:
                params['reasonid'] = reason_id

            slots_data = get("appointments/open", practice_id, token, params=params)

            if slots_data and slots_data.get('appointments'):
                for slot in slots_data['appointments']:
                    all_open_slots.append({
                        'appointmentid': slot.get('appointmentid'),
                        'date': slot.get('date'),
                        'time': slot.get('starttime'),
                        'department': dept.get('name'),
                    })
        
        return JsonResponse(all_open_slots, safe=False)

    except Exception as e:
        # Log the full error for debugging
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


def get_provider_details_ajax(request, providerid):
    try:
        provider = Provider.objects.get(providerid=providerid)
        data = {
            'npi': provider.npi,
            'full_name': provider.full_name.strip() or 'No Name',
            'specialty': provider.specialty or '',
            'subspecialty': provider.subspecialty or '',
            'city': provider.city or '',
            'state': provider.state or '',
            'primary_department': provider.primary_department or '',
            'accepting_new_patients': provider.accepting_new_patients,
        }
        return JsonResponse(data)
    except Provider.DoesNotExist:
        return JsonResponse({'error': 'Provider not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_sorted_providers_ajax(request):
    specialty = request.GET.get('specialty', '')
    
    try:
        user_practice = request.user.userprofile.practice
    except (UserProfile.DoesNotExist, AttributeError):
        user_practice = None

    if user_practice:
        all_providers_qs = Provider.objects.filter(practice=user_practice)
    else:
        all_providers_qs = Provider.objects.all()

    # De-duplicate providers in Python
    unique_providers = []
    seen_names = set()
    for provider in all_providers_qs:
        if provider.full_name not in seen_names:
            unique_providers.append(provider)
            seen_names.add(provider.full_name)

    all_providers = unique_providers

    # Calculate completeness score for all providers
    for provider in all_providers:
        score = 0
        if provider.full_name: score += 1
        if provider.specialty: score += 1
        if provider.subspecialty: score += 1
        if provider.city: score += 1
        if provider.state: score += 1
        if provider.npi: score += 1
        if provider.accepting_new_patients is not None: score += 1
        if provider.primary_department: score += 1
        provider.completeness_score = score

    if specialty:
        # Separate providers into matching and non-matching specialty groups
        matching_specialty_providers = [p for p in all_providers if p.specialty and p.specialty.lower() == specialty.lower()]
        other_providers = [p for p in all_providers if not p.specialty or p.specialty.lower() != specialty.lower()]

        # Sort each group by completeness_score (descending) then full_name (ascending)
        matching_specialty_providers.sort(key=lambda p: (p.completeness_score, p.full_name.strip() or 'No Name'), reverse=True)
        other_providers.sort(key=lambda p: (p.completeness_score, p.full_name.strip() or 'No Name'), reverse=True)

        # Combine, with matching specialty providers first
        providers_to_return = matching_specialty_providers + other_providers
    else:
        # If no specialty selected, sort all providers by completeness_score (descending) then full_name (ascending)
        all_providers.sort(key=lambda p: (p.completeness_score, p.full_name.strip() or 'No Name'), reverse=True)
        providers_to_return = all_providers

    provider_data = []
    for p in providers_to_return:
        provider_data.append({'providerid': p.providerid, 'npi': p.npi, 'full_name': p.full_name.strip() or 'No Name', 'specialty': p.specialty or ''})
    return JsonResponse(provider_data, safe=False)

@login_required
def get_appointment_reasons_ajax(request):
    provider_id = request.GET.get('provider_id')
    department_id = request.GET.get('department_id')

    if not provider_id or not department_id:
        return JsonResponse({'error': 'provider_id and department_id are required'}, status=400)

    try:
        user_practice = request.user.userprofile.practice
        if not user_practice or not user_practice.athena_practice_id:
            return JsonResponse({'error': 'User has no practice ID configured.'}, status=400)
        practice_id = user_practice.athena_practice_id
    except (UserProfile.DoesNotExist, AttributeError):
        return JsonResponse({'error': 'Could not determine user\'s practice.'}, status=400)

    cache_key = f'athena_reasons_{practice_id}_{provider_id}_{department_id}'
    cached_reasons = cache.get(cache_key)

    if cached_reasons:
        return JsonResponse(cached_reasons, safe=False)

    try:
        token = get_token()
        params = {
            'providerid': provider_id,
            'departmentid': department_id,
        }
        reasons_data = get("patientappointmentreasons", practice_id, token, params=params)
        
        reasons_list = []
        if reasons_data and 'patientappointmentreasons' in reasons_data:
            for reason in reasons_data['patientappointmentreasons']:
                reasons_list.append({
                    'id': reason.get('reasonid'),
                    'name': reason.get('reason'),
                })
        
        cache.set(cache_key, reasons_list, 3600) # Cache for 1 hour
        return JsonResponse(reasons_list, safe=False)

    except Exception as e:
        logging.error(f"Error fetching appointment reasons: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_provider_departments_ajax(request, providerid=None):
    try:
        user_practice = request.user.userprofile.practice
        if not user_practice or not user_practice.athena_practice_id:
            return JsonResponse({'error': 'User has no practice ID configured.'}, status=400)
        practice_id = user_practice.athena_practice_id
    except (UserProfile.DoesNotExist, AttributeError):
        return JsonResponse({'error': 'Could not determine user\'s practice.'}, status=400)

    provider_npi = None
    if providerid:
        try:
            provider = Provider.objects.get(providerid=providerid)
            provider_npi = provider.npi
        except Provider.DoesNotExist:
            return JsonResponse({'error': 'Provider not found'}, status=404)

    token = get_token()
    departments_list = []
    usual_dept_id = None

    if provider_npi:
        try:
            provider_details_data = get(f"providers/{provider_npi}", practice_id, token, params={"showusualdepartmentguessthreshold": 0.5})
            if provider_details_data and provider_details_data[0]:
                usual_dept_id = provider_details_data[0].get('usualdepartmentid')
        except Exception as e:
            logging.error(f"Error fetching provider details for NPI {provider_npi}: {e}")
            # Continue to fetch all departments if provider details fail

    # Fetch all departments
    try:
        all_departments_data = get("departments", practice_id, token, params={"limit": 200})
        if all_departments_data and all_departments_data.get('departments'):
            for dept in all_departments_data['departments']:
                departments_list.append({'id': dept.get('departmentid'), 'name': dept.get('name')})
    except Exception as e:
        logging.error(f"Error fetching all departments: {e}")
        return JsonResponse({'error': f'Error fetching all departments: {e}'}, status=500)

    # Sort to put the usual department at the top
    if usual_dept_id:
        departments_list.sort(key=lambda x: str(x.get('id')) != str(usual_dept_id))

    return JsonResponse(departments_list, safe=False)



@login_required
def search_appointment_reasons_ajax(request):
    query = request.GET.get('query', '').strip()
    if not query or len(query) < 2: # API requires at least 2 characters
        return JsonResponse([], safe=False)

    try:
        user_practice = request.user.userprofile.practice
        if not user_practice or not user_practice.athena_practice_id:
            return JsonResponse([], safe=False)
        practice_id = user_practice.athena_practice_id
    except (UserProfile.DoesNotExist, AttributeError):
        return JsonResponse([], safe=False)

    cache_key = f'athena_referral_order_type_search_{query}'
    cached_results = cache.get(cache_key)

    if cached_results:
        return JsonResponse(cached_results, safe=False)

    try:
        token = get_token()
        results = []

        params = {'searchvalue': query}
        logging.info(f"Calling Athena API reference/order/referral with params: {params}")
        
        reasons_data = get("reference/order/referral", practice_id, token, params=params)
        
        logging.info(f"Raw reasons_data from Athena API: {reasons_data}")
        
        if reasons_data: # This endpoint returns a list directly
            for reason in reasons_data:
                results.append({
                    'id': reason.get('ordertypeid'),
                    'name': reason.get('name'),
                })
        
        logging.info(f"Results after processing: {results}")
        
        cache.set(cache_key, results, 300) # Cache for 5 minutes
        return JsonResponse(results, safe=False)

    except Exception as e:
        logging.error(f"Error searching appointment reasons: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def create_referral_order_ajax(request):
    if request.method == 'POST':
        try:
            user_practice = request.user.userprofile.practice
            if not user_practice or not user_practice.athena_practice_id:
                logging.error("User has no practice ID configured.")
                return JsonResponse({'error': 'User has no practice ID configured.'}, status=400)
            practice_id = user_practice.athena_practice_id

            data = json.loads(request.body)
            logging.info(f"Received data for referral order creation: {data}")

            token = get_token()
            patient_id = data['patient_id']
            department_id = data['department_id']
            reason_id = data['reason_id']

            # Step 1.1: Get reason name from reason_id
            # This requires a provider_id and department_id.
            # We need to fetch the reason name to use as searchvalue for ordertypeid.
            # Let's reuse the logic from get_appointment_reasons_ajax to get the reason name.
            provider = Provider.objects.filter(practice=user_practice).first() # Assuming any provider will do to fetch reasons
            if not provider:
                logging.error("No providers found for this practice to fetch reason name.")
                return JsonResponse({'error': 'No providers found for this practice to fetch reason name.'}, status=400)

            reason_name = None
            reasons_data = get("patientappointmentreasons", practice_id, token, params={'providerid': provider.providerid, 'departmentid': department_id})
            if reasons_data and 'patientappointmentreasons' in reasons_data:
                for reason in reasons_data['patientappointmentreasons']:
                    if str(reason.get('reasonid')) == str(reason_id):
                        reason_name = reason.get('reason')
                        break
            
            if not reason_name:
                logging.error(f"Reason name not found for reason_id: {reason_id}")
                return JsonResponse({'error': f'Reason name not found for reason_id: {reason_id}'}, status=400)
            logging.info(f"Found reason name: {reason_name} for reason_id: {reason_id}")

            # Step 1.2: Get ordertypeid using the reason name
            headers = {"Authorization": f"Bearer {token}"}
            params = {'searchvalue': reason_name}
            url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/reference/order/referral"
            logging.info(f"Getting ordertypeid from URL: {url} with params: {params}")
            logging.info(f"Headers for ordertypeid request: {headers}")
            response = requests.get(url, headers=headers, params=params)
            logging.info(f"Response from ordertypeid request: {response.status_code} {response.text}")
            response.raise_for_status()
            referral_order_types = response.json()

            if not referral_order_types or not referral_order_types[0]:
                logging.error("Could not find referral order types.")
                return JsonResponse({'error': 'Could not find referral order types.'}, status=400)
            order_type_id = referral_order_types[0]['ordertypeid']
            logging.info(f"Found ordertypeid: {order_type_id}")

            # Step 2: Create an "Orders Only" encounter
            order_group_payload = {
                'patientid': patient_id,
                'departmentid': department_id,
            }
            encounter_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/chart/{patient_id}/ordergroups"
            logging.info(f"Creating encounter with URL: {encounter_url}")
            logging.info(f"Payload for encounter creation: {order_group_payload}")
            order_group_response = requests.post(encounter_url, headers=headers, data=order_group_payload)
            logging.info(f"Response from encounter creation: {order_group_response.status_code} {order_group_response.text}")
            order_group_response.raise_for_status()
            encounter_id = order_group_response.json().get('encounterid')

            if not encounter_id:
                logging.error("Could not create an encounter.")
                return JsonResponse({'error': 'Could not create an encounter.'}, status=400)
            logging.info(f"Created encounter with ID: {encounter_id}")

            # Step 3: Create the referral order
            referral_order_payload = {
                'diagnosissnomedcode': '3457005', # Patient referral (procedure)
                'ordertypeid': order_type_id,
                'futuresubmitdate': datetime.now().strftime('%m/%d/%Y'),
            }
            
            referral_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/chart/encounter/{encounter_id}/orders/referral"
            referral_headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            logging.info(f"Creating referral order with URL: {referral_url}")
            logging.info(f"Payload for referral order creation: {referral_order_payload}")
            logging.info(f"Headers for referral order creation: {referral_headers}")
            response = requests.post(referral_url, headers=referral_headers, data=referral_order_payload)
            logging.info(f"Response from referral order creation: {response.status_code} {response.text}")
            response.raise_for_status()
            
            athena_referral_id = response.json().get('documentid')
            logging.info(f"Created referral order with Athena ID: {athena_referral_id}")

            # Create local referral
            provider_npi = data['provider_id']
            provider = Provider.objects.get(npi=provider_npi)
            patient, _ = Patient.objects.get_or_create(original_id=patient_id)
            payer_code = data.get('payer_code')
            payer = None
            if payer_code:
                payer, _ = Payer.objects.get_or_create(code=payer_code, defaults={'name': payer_code})

            referral = Referral.objects.create(
                patient=patient,
                provider=provider,
                payer=payer,
                specialty=data.get('specialty') or provider.specialty or '',
                in_network=provider.is_in_network,
                is_urgent=data.get('is_urgent', False),
                status=Referral.Status.SENT,
                referral_date=datetime.now().date(),
                athena_appointment_id=athena_referral_id, # Using this field to store the referral ID
                suggested_provider_ids="" 
            )
            ReferralHistory.objects.create(referral=referral, status=referral.status)
            logging.info(f"Local Referral {referral.id} created for patient {patient.original_id} and provider {provider.npi}.")

            return JsonResponse({'local_referral_id': referral.id, 'athena_referral_id': athena_referral_id}, safe=False)

        except Exception as e:
            logging.error(f"Error creating referral order: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def patient_search_ajax(request):
    query = request.GET.get('query', '').strip()
    if not query:
        return JsonResponse([], safe=False)

    try:
        user_practice = request.user.userprofile.practice
        if not user_practice or not user_practice.athena_practice_id:
            return JsonResponse([], safe=False)
        practice_id = user_practice.athena_practice_id
    except (UserProfile.DoesNotExist, AttributeError):
        return JsonResponse([], safe=False)

    cache_key = f'athena_patient_search_{query}'
    cached_results = cache.get(cache_key)

    if cached_results:
        return JsonResponse(cached_results, safe=False)

    try:
        token = get_token()
        results = []

        # Check if the query is an integer (likely a patient ID)
        try:
            patient_id = int(query)
            # If it is, perform a direct lookup
            patient_data = get(f"patients/{patient_id}", practice_id, token)
            if patient_data and isinstance(patient_data, list) and patient_data[0]:
                patient = patient_data[0]
                results.append({
                    'patientid': patient.get('patientid'),
                    'name': f"{patient.get('firstname', '')} {patient.get('lastname', '')}".strip(),
                })
        except ValueError:
            # If it's not an integer, treat it as a name search
            # Split the query into potential first and last names
            names = query.split()
            firstname = names[0]
            lastname = names[-1] if len(names) > 1 else ''

            params = {
                'firstname': firstname,
                'lastname': lastname,
                'limit': 10, # Limit results to 10
            }
            patients_data = get("patients", practice_id, token, params=params)
            if patients_data and patients_data.get('patients'):
                for patient in patients_data['patients']:
                    results.append({
                        'patientid': patient.get('patientid'),
                        'name': f"{patient.get('firstname', '')} {patient.get('lastname', '')}".strip(),
                    })
        
        cache.set(cache_key, results, 300) # Cache for 5 minutes
        return JsonResponse(results, safe=False)

    except Exception as e:
        logging.error(f"Error searching patients: {e}")
        return JsonResponse({'error': str(e)}, status=500)


from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from decimal import Decimal

from . import athena_client


from django.http import StreamingHttpResponse

# Helper functions for Athena sync
def _sync_providers(practice, in_network_ids):
    token = athena_client.get_token()
    practice_id = practice.athena_practice_id
    
    yield "Fetching provider master list from Athena..."
    providers_data = athena_client.get("providers", practice_id, token, params={"limit": 500})
    if not providers_data or not providers_data.get("providers"):
        yield "No providers found in Athena for this practice."
        return

    provider_count = 0
    for provider_summary in providers_data["providers"]:
        provider_id = str(provider_summary.get('providerid'))
        if not provider_id:
            continue

        is_in_network = provider_id in in_network_ids

        Provider.objects.update_or_create(
            practice=practice, providerid=provider_id,
            defaults={
                'npi': provider_summary.get('npi'),
                'full_name': provider_summary.get('displayname') or f"{provider_summary.get('firstname', '')} {provider_summary.get('lastname', '')}".strip(),
                'firstname': provider_summary.get('firstname'),
                'lastname': provider_summary.get('lastname'),
                'specialty': provider_summary.get('specialty'),
                'is_in_network': is_in_network,
            }
        )
        provider_count += 1
    yield f"Synced {provider_count} providers. Marked {len(in_network_ids)} providers as in-network based on the provided list."

def _sync_referrals(practice):
    token = athena_client.get_token()
    practice_id = practice.athena_practice_id

    practice_provider_ids = list(practice.provider_set.values_list('providerid', flat=True))
    all_patients = Patient.objects.all()
    
    referral_count = 0
    skipped_count = 0
    error_count = 0
    
    yield f"Found {len(all_patients)} patients to check for referrals..."

    for i, patient in enumerate(all_patients):
        if (i + 1) % 10 == 0:
             yield f"Processing patient {i+1} of {len(all_patients)}..."

        if not patient.original_id:
            continue
        try:
            referrals_data = athena_client.get(f"patients/{patient.original_id}/referralauths", practice_id, token, params={"limit": 100})

            if not referrals_data or not referrals_data.get("referralauths"):
                continue

            for auth in referrals_data["referralauths"]:
                referring_provider_id_str = auth.get('referringproviderid')

                if not referring_provider_id_str:
                    skipped_count += 1
                    continue
                
                try:
                    referring_provider_id = int(referring_provider_id_str)
                except (ValueError, TypeError):
                    skipped_count += 1
                    continue

                if referring_provider_id not in practice_provider_ids:
                    skipped_count += 1
                    continue

                try:
                    provider = Provider.objects.get(providerid=referring_provider_id, practice=practice)
                except Provider.DoesNotExist:
                    skipped_count += 1
                    continue

                referral_date_str = auth.get('referralauthdate')
                if not referral_date_str:
                    referral_date = timezone.now().date()
                else:
                    referral_date = datetime.strptime(referral_date_str, '%m/%d/%Y').date()

                Referral.objects.update_or_create(
                    athena_appointment_id=auth.get('referralauthid'),
                    defaults={
                        'patient': patient,
                        'provider': provider,
                        'referral_date': referral_date,
                        'specialty': provider.specialty,
                        'status': (auth.get("referralauthtype") or "pending").lower(),
                        'cost_value': Decimal(auth.get("amount", "0") or "0"),
                    }
                )
                referral_count += 1
        except Exception as e:
            error_count += 1
            logging.error(f"Failed to sync referrals for patient {patient.original_id}: {e}")
            continue
    
    if skipped_count > 0:
        yield f"Skipped {skipped_count} referrals that did not belong to a provider in this practice or had other data issues."
    if error_count > 0:
        yield f"Encountered {error_count} errors fetching patient referral data. See server logs for details."
    
    yield f"Synced {referral_count} referrals."


@login_required
@user_passes_test(lambda u: u.is_superuser)
def sync_stream_view(request):
    practice_id = request.GET.get('practice_id')
    in_network_ids_str = request.GET.get('in_network_provider_ids', '')
    in_network_ids = {pid.strip() for pid in in_network_ids_str.split(',') if pid.strip()}

    def event_stream():
        try:
            practice = Practice.objects.get(id=practice_id)
            yield f"event: message\ndata: Starting sync for {practice.name}...\n\n"
            
            # Sync providers and stream results
            for message in _sync_providers(practice, in_network_ids):
                yield f"event: message\ndata: {message}\n\n"

            # Sync referrals and stream results
            for message in _sync_referrals(practice):
                yield f"event: message\ndata: {message}\n\n"

            yield f"event: message\ndata: Sync complete!\n\n"

        except Practice.DoesNotExist:
            yield f"event: error\ndata: Practice not found.\n\n"
        except Exception as e:
            logging.error(f"An error occurred during Athena sync stream: {e}")
            yield f"event: error\ndata: An error occurred: {e}\n\n"
        finally:
            yield "event: close\ndata: Connection closed\n\n"

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def management(request):
    if request.method == 'POST':
        # Handle Update In-Network
        if 'update_in_network' in request.POST:
            practice_id = request.POST.get('practice_id')
            in_network_ids_str = request.POST.get('in_network_provider_ids', '')
            in_network_ids = {int(pid.strip()) for pid in in_network_ids_str.split(',') if pid.strip().isdigit()}

            try:
                practice = Practice.objects.get(id=practice_id)
                # Reset all providers for this practice
                practice.provider_set.update(is_in_network=False)
                # Set in-network for the provided list
                practice.provider_set.filter(providerid__in=in_network_ids).update(is_in_network=True)
                messages.success(request, f"In-network providers updated for {practice.name}.")
            except Practice.DoesNotExist:
                messages.error(request, "Practice not found.")
            return redirect('management')
    # Handle Create Practice Form
    if 'create_practice' in request.POST:
        name = request.POST.get('name')
        athena_id = request.POST.get('athena_practice_id')
        location = request.POST.get('location')
        if name and athena_id and location:
            practice, created = Practice.objects.get_or_create(
                athena_practice_id=athena_id,
                defaults={'name': name, 'location': location}
            )
            if created:
                messages.success(request, f'Practice "{practice.name}" created successfully.')
            else:
                messages.warning(request, f'Practice with Athena ID "{athena_id}" already exists.')
        else:
            messages.error(request, 'All fields are required to create a practice.')
        return redirect('management')

    # Handle Create User Form
    if 'create_user' in request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        practice_id = request.POST.get('practice_id')
        if username and password and practice_id:
            try:
                practice = Practice.objects.get(id=practice_id)
                try:
                    user = User.objects.get(username=username)
                    user.set_password(password)
                    user.is_active = True
                    user.save()
                    messages.warning(request, f'User "{username}" already existed and has been reactivated. Their password and practice have been updated.')
                except User.DoesNotExist:
                    user = User.objects.create_user(username=username, password=password)
                    messages.success(request, f'User "{username}" created and assigned to {practice.name}.')

                # Update or create the user profile
                profile, _ = UserProfile.objects.update_or_create(
                    user=user,
                    defaults={'practice': practice}
                )

            except Practice.DoesNotExist:
                messages.error(request, "The selected practice does not exist.")
        else:
            messages.error(request, 'All fields are required to create a user.')
        return redirect('management')

    practices = Practice.objects.all()
    return render(request, 'analytics/management.html', {'practices': practices})
def _run_import_athena(practice_id_arg, client_id_arg, client_secret_arg):
    import hashlib
    from datetime import datetime, timedelta
    import requests
    from django.utils import timezone
    from analytics.models import Patient, Provider, Referral, ImportLog
    from analytics.athena_client import get_token # Assuming get_token can be used with client_id/secret

    yield f"Starting import_athena for practice ID: {practice_id_arg}"
    initial_referral_count = Referral.objects.count()
    yield f"Pre-run check: Found {initial_referral_count} existing referrals."
    task_name = "import_athena_appointments"
    current_run_time = timezone.now()

    try:
        last_run = ImportLog.objects.filter(task_name=task_name, status="success").latest("last_run_at")
        start_date = last_run.last_run_at.date()
        yield f"Last successful run was on {start_date:%Y-%m-%d}. Fetching changes since then."
    except ImportLog.DoesNotExist:
        start_date = (current_run_time - timedelta(days=30)).date()
        yield "No previous successful run found. Fetching data for the last 30 days."
    end_date = current_run_time.date()

    token_url = "https://api.preview.platform.athenahealth.com/oauth2/v1/token"
    try:
        token_resp = requests.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id_arg,
                "client_secret": client_secret_arg,
                "scope": "system/CarePlan.read",
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]
    except requests.RequestException as e:
        ImportLog.objects.create(task_name=task_name, last_run_at=current_run_time, status="failed", notes=f"Token Error: {e}")
        yield f"Failed to obtain OAuth token: {e}"
        return

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        provider_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id_arg}/providers"
        response = requests.get(provider_url, headers=headers)
        response.raise_for_status()
        providers_data = response.json().get("providers", [])

        provider_count = 0
        for provider_data in providers_data:
            provider_id = str(provider_data.get("providerid"))
            if not provider_id: continue

            _, created = Provider.objects.update_or_create(
                npi=provider_id, 
                defaults={
                    "full_name": provider_data.get("displayname") or f"Provider {provider_id}",
                    "providerid": provider_id # Ensure providerid is set
                }
            )
            if created:
                provider_count += 1
        yield f"Found and created {provider_count} new providers."

    except requests.RequestException as e:
        yield f"Failed to fetch providers: {e}"
        return

    try:
        all_appointments = []
        dept_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id_arg}/departments"
        departments = requests.get(dept_url, headers=headers).json().get("departments", [])

        for dept in departments:
            department_id = dept['departmentid']
            yield f"Fetching appointments for Department ID: {department_id}..."
            
            params = {
                "departmentid": department_id,
                "startdate": start_date.isoformat(),
                "enddate": end_date.isoformat(),
            }
            appt_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id_arg}/appointments/booked"
            response = requests.get(appt_url, headers=headers, params=params)
            response.raise_for_status()
            all_appointments.extend(response.json().get("appointments", []))

        yield f"Found {len(all_appointments)} total appointments to process."
    except requests.RequestException as e:
        ImportLog.objects.create(task_name=task_name, last_run_at=current_run_time, status="failed", notes=f"API Error: {e}")
        yield f"Failed to fetch appointments: {e}"
        return
    created_count = 0
    for appt in all_appointments:
        patient_id = str(appt.get("patientid"))
        if not patient_id: continue

        patient, _ = Patient.objects.get_or_create(
            original_id=patient_id,
            defaults={
                "pseudonym": hashlib.sha256(patient_id.encode()).hexdigest()
            },
        )
        provider_id = str(appt.get("providerid") or "")
        if not provider_id: continue
        provider, _ = Provider.objects.get_or_create(
            npi=provider_id, defaults={
                "full_name": f"Provider {provider_id}",
                "providerid": provider_id # Ensure providerid is set
            }
        )

        ref_date_str = appt.get("date")
        if ref_date_str:
            try:
                ref_date = datetime.strptime(ref_date_str, "%m/%d/%Y").date()
            except ValueError:
                yield f"Invalid date format '{ref_date_str}'. Using current date."
                ref_date = timezone.now().date()
        else:
            yield f"No creation date from API. Using current date."
            ref_date = timezone.now().date()
        _, created = Referral.objects.update_or_create(
            patient=patient, provider=provider, referral_date=ref_date,
            defaults={
                "status": Referral.Status.PENDING
            }
        )
        yield f"Processed Referral: PatientID={patient.original_id}, ProviderID={provider_id}, ReferralDate={ref_date}, Created={created}"
        if created:
            created_count += 1
    ImportLog.objects.update_or_create(
        task_name=task_name,
        defaults={
            "last_run_at": current_run_time, 
            "status": "success",
            "notes": f"Imported {created_count} new referrals."
        }
    )
    yield f"Import complete. Created {created_count} new referrals."

def _run_import_athena_data(practice_id_arg, page_size_arg=25):
    from decimal import Decimal
    from django.core.paginator import Paginator
    from analytics.models import Provider, Patient, Referral, Payer
    from analytics.athena_client import get_token, get
    from datetime import datetime
    from django.utils import timezone

    yield f"Starting import_athena_data for practice ID: {practice_id_arg} with page size: {page_size_arg}"
    token = get_token()
    all_providers = list(Provider.objects.all())
    if not all_providers:
        yield "No providers found. Please run import_athena first."
        return

    yield "Importing referral authorizations..."
    all_patients = Patient.objects.all().order_by('id')
    paginator = Paginator(all_patients, page_size_arg)
    total_created = 0
    total_updated = 0

    for page_num in paginator.page_range:
        yield f"-- Processing page {page_num} of {paginator.num_pages} --"
        for patient in paginator.page(page_num).object_list:
            insurances_data = None
            try:
                insurances_data = get(f"patients/{patient.original_id}/insurances", practice_id_arg, token)
            except Exception as e:
                yield f"API error for patient {patient.original_id} insurances: {e}. Skipping insurance data."

            eligibility_by_payer = {}
            if insurances_data and insurances_data.get("insurances"):
                eligibility_by_payer = {
                    str(ins.get("insurancepackageid")): ins.get("eligibilitystatus", "").lower() == "eligible"
                    for ins in insurances_data.get("insurances", [])
                }

            try:
                referral_to_update = Referral.objects.filter(
                    patient=patient,
                    status=Referral.Status.PENDING
                ).latest('referral_date')
            except Referral.DoesNotExist:
                continue

            refauths_data = None
            try:
                refauths_data = get(f"patients/{patient.original_id}/referralauths", practice_id_arg, token)
            except Exception as e:
                yield f"API error for patient {patient.original_id} referral auths: {e}. Skipping referral auth data."

            auth = None
            if refauths_data and refauths_data.get("referralauths"):
                if not referral_to_update.provider:
                    yield f"Referral {referral_to_update.id} has no provider. Skipping update."
                    continue

                provider_npi = referral_to_update.provider.npi
                for ra_auth in refauths_data.get("referralauths", []):
                    if str(ra_auth.get("referringproviderid")) == provider_npi:
                        auth = ra_auth
                        break

            if not auth:
                yield f"No live referral auth data found for referral {referral_to_update.id}. Skipping update."
                continue

            payer_code = list(eligibility_by_payer.keys())[0] if eligibility_by_payer else None
            payer = None
            if payer_code:
                payer, _ = Payer.objects.get_or_create(code=payer_code, defaults={"name": f"Payer {payer_code}"})

            is_in_network = eligibility_by_payer.get(payer_code, False) if payer_code else False
            status = (auth.get("referralauthtype") or "pending").lower()
            if status not in Referral.Status.values: status = Referral.Status.PENDING

            referral_to_update.status = status
            referral_to_update.in_network = is_in_network
            referral_to_update.payer = payer
            referral_to_update.cost_value = Decimal(auth.get("amount", "0") or "0")
            
            ack_at_str = auth.get("acknowledged_at")
            referral_to_update.ack_at = datetime.strptime(ack_at_str, "%Y-%m-%dT%H:%M:%SZ") if ack_at_str else None

            scheduled_at_str = auth.get("scheduled_at")
            referral_to_update.scheduled_at = datetime.strptime(scheduled_at_str, "%Y-%m-%dT%H:%M:%SZ") if scheduled_at_str else None
            completed_at_str = auth.get("completed_at")
            referral_to_update.completed_at = datetime.strptime(completed_at_str, "%Y-%m-%dT%H:%M:%SZ") if completed_at_str else None
            cancelled_at_str = auth.get("cancelled_at")
            referral_to_update.cancelled_at = datetime.strptime(cancelled_at_str, "%Y-%m-%dT%H:%M:%SZ") if cancelled_at_str else None
            referral_to_update.save()
            total_updated += 1
            yield f"Import complete. Updated {total_updated} referrals."
            if provider_detail.get("displayname"):
                provider.full_name = provider_detail.get("displayname")
            else:
                provider.full_name = f"{provider_detail.get('firstname', '')} {provider_detail.get('lastname', '')}"
            provider.specialty = provider_detail.get("specialty")
            provider.subspecialty = provider_detail.get("specialty2")
            department_id = provider_detail.get("usualdepartmentid")
            if department_id:
                try:
                    department_data_list = get(f"departments/{department_id}", practice_id_arg, token)
                    if department_data_list:
                        department_data = department_data_list[0]
                        provider.city = department_data.get("city")
                        provider.state = department_data.get("state")
                        provider.primary_department = department_data.get("name")
                        yield f"Set primary department for {provider.full_name} to {provider.primary_department}"
                        if department_data.get("ishospitaldepartment"):
                            hospital, _ = Hospital.objects.get_or_create(name=department_data.get("name"))
                            # provider.hospital_affiliations.add(hospital) # Assuming M2M field exists
                except requests.RequestException as e:
                    yield f"API error for department {department_id}: {e}. Skipping location data."
                    provider.accepting_new_patients = provider_detail.get("acceptingnewpatients")
                    provider.save()
                    updated_count += 1
                except Provider.DoesNotExist:
                    yield f"Provider with ID {provider_id} not found in local DB. Skipping update."
                except requests.RequestException as e:
                    yield f"API error for provider {provider_id}: {e}. Skipping provider."
                    yield f"Successfully updated {updated_count} providers."
                except requests.RequestException as e:
                    yield f"Failed to fetch providers: {e}"

def _run_import_provider_data(practice_id_arg):
    import subprocess
    import sys
    from django.conf import settings

    command = [
        sys.executable,
        str(settings.BASE_DIR / "manage.py"),
        "import_provider_data",
        f"--practice_id={practice_id_arg}",
    ]

    yield f"Running command: {' '.join(command)}"

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    for line in process.stdout:
        yield line.strip()

    process.wait()

    if process.returncode == 0:
        yield "Command finished successfully."
    else:
        yield f"Command failed with return code {process.returncode}."


@login_required
@user_passes_test(lambda u: u.is_superuser)
def stream_command_view(request):
    command_name = request.GET.get('command')
    practice_id = request.GET.get('practice_id')
    client_id = request.GET.get('client_id')
    client_secret = request.GET.get('client_secret')
    page_size = request.GET.get('page_size')
    def event_stream():
        if command_name == 'import_provider_data':
            for message in _run_import_provider_data(practice_id):
                yield f"event: message\ndata: {message}\n\n"
        elif command_name == 'import_athena':
            for message in _run_import_athena(practice_id, client_id, client_secret):
                yield f"event: message\ndata: {message}\n\n"
        elif command_name == 'import_athena_data':
            for message in _run_import_athena_data(practice_id, int(page_size) if page_size else 25):
                yield f"event: message\ndata: {message}\n\n"
        else:
            yield f"event: message\ndata: Unknown command: {command_name}\n\n"
        yield "event: close\ndata: Connection closed\n\n"
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
# --- Delete referral ---
def delete_referral(request, pk):
    """
    Delete a referral by its primary key.  Redirect back to the dashboard.
    """
    referral = get_object_or_404(Referral, pk=pk)
    referral.delete()
    return redirect('analytics_dashboard')