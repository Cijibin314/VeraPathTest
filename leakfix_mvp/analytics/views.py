from django.shortcuts import render, redirect, get_object_or_404
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
)
from .forms import ReferralForm
from analytics.ai_utils import generate_suggestions
import logging

# --- KPI dashboard ---
def dashboard(request):
    total = Referral.objects.count()
    in_network = Referral.objects.filter(in_network=True).count()
    out_network = Referral.objects.filter(in_network=False).count()
    leakage_cost = (
        Referral.objects.filter(in_network=False).aggregate(total_leak=Sum('cost_value')).get('total_leak')
        or 0
    )
    # New: average leakage cost across all referrals
    avg_leakage_cost = (leakage_cost / out_network) if out_network else 0

    durations_completion = [
        (ref.completed_at.date() - ref.referral_date).days
        for ref in Referral.objects.filter(completed_at__isnull=False)
    ]
    median_days_completion = median(durations_completion) if durations_completion else 0

    durations_ack = [
        (ref.ack_at.date() - ref.referral_date).days
        for ref in Referral.objects.filter(ack_at__isnull=False)
    ]
    median_days_ack = median(durations_ack) if durations_ack else 0

    durations_sched = [
        (ref.scheduled_at.date() - ref.referral_date).days
        for ref in Referral.objects.filter(scheduled_at__isnull=False)
    ]
    median_days_schedule = median(durations_sched) if durations_sched else 0

    attempts = [ref.history.count() for ref in Referral.objects.filter(scheduled_at__isnull=False)]
    avg_attempts = (sum(attempts) / len(attempts)) if attempts else 0

    in_network_rate = (in_network / total * 100.0) if total else 0
    completed = Referral.objects.filter(status=Referral.Status.COMPLETED).count()
    completion_rate = (completed / total * 100.0) if total else 0

    top_leakage = (
        Referral.objects.filter(in_network=False)
        .values('provider__full_name')
        .annotate(total_leak=Sum('cost_value'))
        .order_by('-total_leak')[:5]
    )

    top_payer_leakage = (
        Referral.objects.filter(in_network=False, payer__isnull=False)
        .values('payer__name')
        .annotate(total_leak=Sum('cost_value'))
        .order_by('-total_leak')[:5]
    )

    avg_in_cost = Referral.objects.filter(in_network=True).aggregate(avg=Avg('cost_value'))['avg'] or 0
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
    }
    return render(request, 'analytics/dashboard.html', context)


import json
import os
from django.conf import settings
from django.http import JsonResponse

from django.db.models.functions import Coalesce

# --- Provider list ---
def provider_list(request):
    # Load ACO rules from ACO.txt
    aco_rules = {}
    aco_file_path = os.path.join(settings.BASE_DIR.parent, 'ACO.txt')
    try:
        with open(aco_file_path, 'r') as f:
            aco_rules = json.load(f)
    except FileNotFoundError:
        print(f"[ACO_DEBUG] ACO.txt not found at {aco_file_path}")
        pass # Handle case where ACO.txt doesn't exist

    in_network_providers_names = set(aco_rules.get('in-network_providers', []))
    aco_location = aco_rules.get('location', '')
    aco_city = aco_location.split(',')[0].strip() if aco_location else ''
    aco_state = aco_location.split(',')[1].strip() if aco_location else ''
    preferred_payers_names = set(aco_rules.get('preferred_payers', []))

    providers = list(Provider.objects.all())
    for provider in providers:
        score = 0
        is_preferred = False

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
        print(f"Provider: {provider.full_name}, Score: {provider.completeness_score}")

        # Apply ACO rules for 'is_preferred'
        if provider.full_name in in_network_providers_names or \
           (aco_city and aco_state and provider.city == aco_city and provider.state == aco_state):
            is_preferred = True

        provider.is_preferred = is_preferred

    # Sort: preferred providers first, then by completeness score
    providers.sort(key=lambda p: (p.is_preferred, p.completeness_score), reverse=True)

    return render(request, 'analytics/provider_list.html', {'providers': providers})


# --- Provider search ---
def provider_search(request):
    query = request.GET.get('q', '').strip()
    providers = Provider.objects.all()

    if query:
        providers = providers.filter(
            Q(full_name__icontains=query)
            | Q(specialty__icontains=query)
            | Q(subspecialty__icontains=query)
            | Q(city__icontains=query)
            | Q(state__icontains=query)
            | Q(primary_department__icontains=query)
        )
    
    # Load ACO rules from ACO.txt
    aco_rules = {}
    aco_file_path = os.path.join(settings.BASE_DIR.parent, 'ACO.txt')
    try:
        with open(aco_file_path, 'r') as f:
            aco_rules = json.load(f)
    except FileNotFoundError:
        pass # Handle case where ACO.txt doesn't exist

    in_network_providers_names = set(aco_rules.get('in-network_providers', []))
    aco_location = aco_rules.get('location', '')
    aco_city = aco_location.split(',')[0].strip() if aco_location else ''
    aco_state = aco_location.split(',')[1].strip() if aco_location else ''
    preferred_payers_names = set(aco_rules.get('preferred_payers', []))

    # Calculate is_preferred and completeness_score for each provider object
    for provider in providers:
        score = 0
        is_preferred = False

        # Completeness score calculation
        if provider.full_name: score += 1
        if provider.specialty: score += 1
        if provider.subspecialty: score += 1
        if provider.city: score += 1
        if provider.state: score += 1
        if provider.npi: score += 1
        if provider.accepting_new_patients is not None: score += 1
        if provider.primary_department: score += 1
        provider.completeness_score = score

        # Apply ACO rules for 'is_preferred'
        if provider.full_name in in_network_providers_names or \
           (aco_city and aco_state and provider.city == aco_city and provider.state == aco_state):
            is_preferred = True

        provider.is_preferred = is_preferred

    # Sort: preferred providers first, then by completeness score
    providers = list(providers) # Convert queryset to list for sorting
    providers.sort(key=lambda p: (p.is_preferred, p.completeness_score), reverse=True)

    # Convert Provider objects to dictionaries for JSON response
    data = []
    for provider in providers:
        data.append({
            'full_name': provider.full_name,
            'specialty': provider.specialty,
            'subspecialty': provider.subspecialty,
            'primary_department': provider.primary_department,
            'location': f"{provider.city}, {provider.state}" if provider.city and provider.state else '',
            'npi': provider.npi,
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
def create_referral(request):
    if request.method == 'POST':
        form = ReferralForm(request.POST)
        if form.is_valid():
            # Load ACO rules to determine in-network status
            aco_rules = {}
            aco_file_path = os.path.join(settings.BASE_DIR.parent, 'ACO.txt')
            try:
                with open(aco_file_path, 'r') as f:
                    aco_rules = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass # If file is missing or invalid, treat all as out-of-network

            in_network_providers_npi = set(str(n) for n in aco_rules.get('in-network_providers', []))

            provider = form.cleaned_data['provider']
            is_in_network = str(provider.npi) in in_network_providers_npi

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
                in_network=is_in_network, # Set automatically
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
from .athena_client import get_token, get
from datetime import datetime, timedelta
from django.core.cache import cache

def find_provider_slots(request):
    provider_id_str = request.GET.get('provider_id')
    reason_id_str = request.GET.get('reasonid')
    search_date_str = request.GET.get('search_date') # New parameter

    if not provider_id_str:
        return JsonResponse({'error': 'provider_id is required'}, status=400)

    try:
        provider_id = int(provider_id_str)
        reason_id = int(reason_id_str) if reason_id_str else None

        token = get_token()
        practice_id = '195900' 
        
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
            # Create a unique cache key for this specific API call
            cache_key = f'athena_open_slots_{practice_id}_{dept_id}_{provider_id}_{start_date}_{end_date}_{reason_id}'
            cached_slots_data = cache.get(cache_key)

            if cached_slots_data:
                slots_data = cached_slots_data
            else:
                params = {
                    "departmentid": dept_id,
                    "providerid": provider_id,
                    "startdate": start_date,
                    "enddate": end_date,
                }
                if reason_id:
                    params['reasonid'] = reason_id

                slots_data = get("appointments/open", practice_id, token, params=params)
                # Cache the response for 5 minutes
                cache.set(cache_key, slots_data, 300)

            if slots_data and slots_data.get('appointments'):
                for slot in slots_data.get('appointments'):
                    all_open_slots.append({
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


def get_provider_details_ajax(request, npi):
    try:
        provider = Provider.objects.get(npi=npi)
        logging.info(f"Raw full_name for NPI {provider.npi} in get_provider_details_ajax: '{provider.full_name}'")
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
    
    all_providers = list(Provider.objects.all())

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
        logging.info(f"Raw full_name for NPI {p.npi} in get_sorted_providers_ajax: '{p.full_name}'")
        provider_data.append({'npi': p.npi, 'full_name': p.full_name.strip() or 'No Name', 'specialty': p.specialty or ''})
    return JsonResponse(provider_data, safe=False)

def get_appointment_reasons_ajax(request):
    provider_id = request.GET.get('provider_id')
    department_id = request.GET.get('department_id')

    if not provider_id or not department_id:
        return JsonResponse({'error': 'provider_id and department_id are required'}, status=400)

    practice_id = '195900'
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

def get_provider_departments_ajax(request, npi=None):
    practice_id = '195900'
    token = get_token()
    departments_list = []
    usual_dept_id = None

    if npi:
        provider_details_data = get(f"providers/{npi}", practice_id, token, params={"showusualdepartmentguessthreshold": 0.5})
        if provider_details_data and provider_details_data[0]:
            usual_dept_id = provider_details_data[0].get('usualdepartmentid')

    # Fetch all departments
    all_departments_data = get("departments", practice_id, token, params={"limit": 200})
    if all_departments_data and all_departments_data.get('departments'):
        for dept in all_departments_data['departments']:
            departments_list.append({'id': dept.get('departmentid'), 'name': dept.get('name')})

    # Sort to put the usual department at the top
    if usual_dept_id:
        departments_list.sort(key=lambda x: str(x.get('id')) != str(usual_dept_id))

    return JsonResponse(departments_list, safe=False)


# --- Delete referral ---
def delete_referral(request, pk):
    """
    Delete a referral by its primary key.  Redirect back to the dashboard.
    """
    referral = get_object_or_404(Referral, pk=pk)
    referral.delete()
    return redirect('analytics_dashboard')
