import difflib
from urllib.parse import urlencode
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Sum, Q, Avg, Value
from django.db.models.functions import Concat
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


@login_required
def referral_list(request):
    try:
        user_practice = request.user.userprofile.practice
    except (UserProfile.DoesNotExist, AttributeError):
        user_practice = None

    if user_practice:
        referrals = Referral.objects.filter(provider__practice=user_practice)
    else:
        referrals = Referral.objects.all()

    query = request.GET.get('q')
    if query:
        referrals = referrals.annotate(
            patient_full_name=Concat('patient__first_name', Value(' '), 'patient__last_name')
        ).filter(
            Q(patient__original_id__icontains=query) |
            Q(patient__pseudonym__icontains=query) |
            Q(patient_full_name__icontains=query) |
            Q(provider__full_name__icontains=query) |
            Q(specialty__icontains=query) |
            Q(status__icontains=query)
        )

    context = {
        'referrals': referrals.order_by('-referral_date'),
        'query': query,
    }
    return render(request, 'analytics/referral_list.html', context)


def referral_detail(request, pk):
    referral = get_object_or_404(Referral, pk=pk)
    return render(request, 'analytics/referral_detail.html', {'referral': referral})

@login_required
def referral_detail_api(request, pk):
    try:
        referral = get_object_or_404(Referral, pk=pk)
        user_practice = request.user.userprofile.practice
        if not user_practice or not user_practice.athena_practice_id:
            return JsonResponse({'error': 'User has no practice ID configured.'}, status=400)
        practice_id = user_practice.athena_practice_id
        
        encounter_id = referral.athena_encounter_id
        order_id = referral.athena_document_id

        if not encounter_id or not order_id:
            return JsonResponse({'error': 'Referral is missing the Athena encounter or order ID.'}, status=400)

        token = get_token()
        
        request_url = f"chart/encounter/{encounter_id}/orders"
        logging.info(f"Making Athena API call to: {request_url} with order_id: {order_id}")
        orders_data = get(request_url, practice_id, token)

        if orders_data and isinstance(orders_data, list) and len(orders_data) > 0:
            # The response is a list containing one object, which contains the 'orders' list.
            order_list = orders_data[0].get('orders', [])
            for order in order_list:
                if str(order.get('orderid')) == str(order_id):
                    return JsonResponse(order)
        
        return JsonResponse({'error': f'Order ID {order_id} not found in encounter {encounter_id}.'}, status=404)

    except Exception as e:
        logging.error(f"A critical error occurred in referral_detail_api: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)


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
    department_id_str = request.GET.get('department_id')
    start_date_str = request.GET.get('startdate')
    end_date_str = request.GET.get('enddate')

    if not provider_id_str or not department_id_str:
        return JsonResponse({'error': 'provider_id and department_id are required'}, status=400)

    try:
        user_practice = request.user.userprofile.practice
        if not user_practice or not user_practice.athena_practice_id:
            return JsonResponse({'error': 'User has no practice ID configured.'}, status=400)
        practice_id = user_practice.athena_practice_id

        provider_id = int(provider_id_str)
        department_id = int(department_id_str)

        token = get_token()
        
        # Step 1: Get all appointment reasons for the provider and department
        reason_params = {'providerid': provider_id, 'departmentid': department_id}
        reasons_data = get("patientappointmentreasons", practice_id, token, params=reason_params)
        
        all_reason_ids = []
        if reasons_data and 'patientappointmentreasons' in reasons_data:
            all_reason_ids = [str(r['reasonid']) for r in reasons_data['patientappointmentreasons']]

        if not all_reason_ids:
            logging.warning(f"No appointment reasons found for provider {provider_id} and department {department_id}. Cannot search for slots.")
            return JsonResponse([], safe=False) # Return empty list if no reasons found

        # Step 2: Find open slots by looping through each reason ID
        all_open_slots = []
        seen_appointment_ids = set()
        
        if start_date_str and end_date_str:
            start_date = start_date_str
            end_date = end_date_str
        else:
            start_date = datetime.now().strftime("%m/%d/%Y")
            end_date = (datetime.now() + timedelta(days=90)).strftime("%m/%d/%Y")

        # Get department name for the response
        department_details = get(f"departments/{department_id}", practice_id, token)
        department_name = department_details[0].get('name') if department_details else f"Department {department_id}"

        for reason_id in all_reason_ids:
            slot_params = {
                "departmentid": department_id,
                "providerid": provider_id,
                "startdate": start_date,
                "enddate": end_date,
                "reasonid": reason_id
            }

            try:
                slots_data = get("appointments/open", practice_id, token, params=slot_params)

                if slots_data and slots_data.get('appointments'):
                    for slot in slots_data['appointments']:
                        appointment_id = slot.get('appointmentid')
                        if appointment_id not in seen_appointment_ids:
                            all_open_slots.append({
                                'appointmentid': appointment_id,
                                'date': slot.get('date'),
                                'time': slot.get('starttime'),
                                'department': department_name,
                            })
                            seen_appointment_ids.add(appointment_id)
            except Exception as e:
                logging.error(f"Could not fetch slots for reasonid {reason_id}: {e}")
                # Continue to the next reason id even if one fails
                continue
        
        return JsonResponse(all_open_slots, safe=False)

    except Exception as e:
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

    if cached_results:
        return JsonResponse(cached_results, safe=False)

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
            provider = Provider.objects.get(providerid=providerid, practice=user_practice)
            provider_npi = provider.npi
        except Provider.DoesNotExist:
            return JsonResponse({'error': 'Provider not found in your practice'}, status=404)
        except Provider.MultipleObjectsReturned:
             # This case should ideally not happen if the unique_together constraint is enforced
             return JsonResponse({'error': 'Multiple providers found with this ID in your practice.'}, status=400)

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
            order_type_id = data['ordertypeid'] # Directly use ordertypeid from the form

            if not order_type_id:
                logging.error("ordertypeid is missing from the request.")
                return JsonResponse({'error': 'Referral Order Type is required.'}, status=400)

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }

            # Step 1: Create an "Orders Only" encounter
            order_group_payload = {
                'patientid': patient_id,
                'departmentid': department_id,
            }
            encounter_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/chart/{patient_id}/ordergroups"
            logging.info(f"Creating encounter with URL: {encounter_url} and payload: {order_group_payload}")
            order_group_response = requests.post(encounter_url, headers=headers, data=urlencode(order_group_payload))
            
            try:
                order_group_response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logging.error(f"Athena API Error (Encounter Creation): {order_group_response.text}")
                raise e

            encounter_id = order_group_response.json().get('encounterid')

            if not encounter_id:
                logging.error("Could not create an encounter.")
                return JsonResponse({'error': 'Could not create an encounter.'}, status=400)
            logging.info(f"Created encounter with ID: {encounter_id}")

            # Step 2: Add a diagnosis to the encounter
            diagnosis_code = '3457005'
            diagnosis_payload = {'snomedcode': diagnosis_code}
            diagnosis_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/chart/encounter/{encounter_id}/diagnoses"
            diagnosis_headers = headers # Re-use the same headers
            logging.info(f"Adding diagnosis to encounter with URL: {diagnosis_url} and payload: {diagnosis_payload}")
            diagnosis_response = requests.post(diagnosis_url, headers=diagnosis_headers, data=urlencode(diagnosis_payload))
            
            try:
                diagnosis_response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logging.error(f"Athena API Error (Diagnosis Creation): {diagnosis_response.text}")
                raise e
            
            logging.info(f"Successfully added diagnosis to encounter {encounter_id}.")

            # Step 3: Verify the diagnosis was added
            time.sleep(3) # Wait for Athena to process the diagnosis
            verify_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/chart/encounter/{encounter_id}/diagnoses"
            logging.info(f"Verifying diagnosis with URL: {verify_url}")
            verify_response = requests.get(verify_url, headers=headers)
            verify_response.raise_for_status()
            diagnoses_data = verify_response.json()
            if isinstance(diagnoses_data, dict):
                diagnoses = diagnoses_data.get('diagnoses', [])
            else:
                diagnoses = diagnoses_data # Assume it's a list
            
            if not any(str(d.get('snomedcode')) == diagnosis_code for d in diagnoses):
                logging.error(f"Verification failed: Diagnosis {diagnosis_code} not found on encounter {encounter_id}. Found: {diagnoses}")
                raise Exception("Diagnosis verification failed.")
            
            logging.info(f"Successfully verified diagnosis on encounter {encounter_id}.")

            # Step 4: Create the referral order document
            referral_order_payload = {
                'ordertypeid': order_type_id,
                'dateofservice': data.get('dateofservice', datetime.now().strftime('%m/%d/%Y')),
                'diagnosissnomedcode': diagnosis_code,
                'highpriority': data.get('is_urgent', False),
                'providernote': data.get('providernote', ''),
                'notetopatient': data.get('notetopatient', ''),
            }
            
            referral_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/chart/encounter/{encounter_id}/orders/referral"
            referral_headers = headers # Re-use the same headers
            logging.info(f"Creating referral order document with URL: {referral_url} and payload: {referral_order_payload}")
            response = requests.post(referral_url, headers=referral_headers, data=urlencode(referral_order_payload))
            
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logging.error(f"Athena API Error Response (Referral Order Document): {response.text}")
                raise e

            athena_document_id = response.json().get('documentid')
            logging.info(f"Created referral order document with Athena ID: {athena_document_id}")

            # --- Update local object with whatever data we can get from the order summary ---
            order_summary = None
            try:
                orders_data = get(f"chart/encounter/{encounter_id}/orders", practice_id, token)
                if orders_data and isinstance(orders_data, list):
                    for order in orders_data:
                        if str(order.get('orderid')) == str(athena_document_id):
                            order_summary = order
                            break
            except Exception as e:
                logging.error(f"Could not retrieve order summary after creation. Will rely on local data. Error: {e}")
            
            # Create local referral, preferring API data but falling back to form data
            status = order_summary.get('status', 'SENT').lower() if order_summary else Referral.Status.SENT
            specialty = order_summary.get('specialty', data.get('specialty')) if order_summary else data.get('specialty')

            # Notes are not in the summary, so we must use the data from our form.
            provider_note = data.get('providernote', '')
            note_to_patient = data.get('notetopatient', '')

            # Create local referral
            provider_npi = data['provider_id']
            provider = Provider.objects.get(npi=provider_npi)
            patient, _ = Patient.objects.get_or_create(original_id=patient_id)
            
            payer = None
            patient_insurance_id = data.get('patientinsuranceid')
            if patient_insurance_id:
                try:
                    payer, _ = Payer.objects.get_or_create(code=patient_insurance_id, defaults={'name': f"Payer ID {patient_insurance_id}"})
                except Exception as e:
                    logging.error(f"Could not create or get Payer object for ID {patient_insurance_id}: {e}")

            referral = Referral.objects.create(
                patient=patient,
                provider=provider,
                payer=payer,
                specialty=specialty or provider.specialty or '',
                in_network=provider.is_in_network,
                is_urgent=data.get('is_urgent', False),
                status=status,
                referral_date=datetime.now().date(),
                athena_document_id=athena_document_id, # Storing the order/document ID
                athena_encounter_id=encounter_id, # Storing the encounter ID
                provider_note=provider_note,
                note_to_patient=note_to_patient,
            )
            ReferralHistory.objects.create(referral=referral, status=referral.status)
            logging.info(f"Local Referral {referral.id} created for patient {patient.original_id} and provider {provider.npi}.")

            return JsonResponse({'local_referral_id': referral.id}, safe=False)

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
            results = []
            results_set = set() # Use a set to store unique patient IDs to avoid duplicates
            
            # Attempt 1: Split query into first and last name
            names = query.split(maxsplit=1)
            firstname_part = names[0]
            lastname_part = names[1] if len(names) > 1 else ''

            params1 = {
                'firstname': firstname_part,
                'lastname': lastname_part,
                'limit': 10,
            }
            patients_data1 = get("patients", practice_id, token, params=params1)
            if patients_data1 and patients_data1.get('patients'):
                for patient in patients_data1['patients']:
                    patient_id = patient.get('patientid')
                    if patient_id not in results_set:
                        results.append({
                            'patientid': patient_id,
                            'name': f"{patient.get('firstname', '')} {patient.get('lastname', '')}".strip(),
                        })
                        results_set.add(patient_id)

            # Attempt 2: As a fallback, search only by the first name part.
            # This helps when a partial last name is typed that the API won't match.
            if lastname_part: # Only run this second query if there was a last name part
                params2 = {
                    'firstname': firstname_part,
                    'limit': 10,
                }
                patients_data2 = get("patients", practice_id, token, params=params2)
                if patients_data2 and patients_data2.get('patients'):
                    
                    # Calculate similarity score for fuzzy sorting
                    scored_patients = []
                    for patient in patients_data2['patients']:
                        patient_id = patient.get('patientid')
                        if patient_id not in results_set:
                            last_name = patient.get('lastname', '')
                            score = difflib.SequenceMatcher(None, lastname_part.lower(), last_name.lower()).ratio()
                            scored_patients.append((patient, score))
                    
                    # Sort by score descending
                    scored_patients.sort(key=lambda x: x[1], reverse=True)

                    # Append sorted, scored patients to results
                    for patient, score in scored_patients:
                        patient_id = patient.get('patientid')
                        # Final check for duplicates though it should be handled by the set
                        if patient_id not in results_set:
                            results.append({
                                'patientid': patient_id,
                                'name': f"{patient.get('firstname', '')} {patient.get('lastname', '')}".strip(),
                            })
                            results_set.add(patient_id)
        
        cache.set(cache_key, results, 300) # Cache for 5 minutes
        return JsonResponse(results, safe=False)

    except Exception as e:
        logging.error(f"Error searching patients: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_patient_insurances_ajax(request, patient_id):
    logging.info(f"Fetching insurances for patient ID: {patient_id}")
    try:
        user_practice = request.user.userprofile.practice
        if not user_practice or not user_practice.athena_practice_id:
            return JsonResponse({'error': 'User has no practice ID configured.'}, status=400)
        practice_id = user_practice.athena_practice_id
    except (UserProfile.DoesNotExist, AttributeError):
        return JsonResponse({'error': 'Could not determine user\'s practice.'}, status=400)

    cache_key = f'athena_patient_insurances_{patient_id}'
    cached_insurances = cache.get(cache_key)
    if cached_insurances:
        logging.info("Returning cached insurance data.")
        return JsonResponse(cached_insurances, safe=False)

    try:
        token = get_token()
        insurances_data = get(f"patients/{patient_id}/insurances", practice_id, token)
        logging.info(f"Raw insurance data from Athena for patient {patient_id}: {insurances_data}")
        
        insurance_list = []
        if insurances_data and 'insurances' in insurances_data:
            for ins in insurances_data['insurances']:
                insurance_list.append({
                    'id': ins.get('insuranceid'),
                    'name': ins.get('insuranceplanname'),
                })
        
        logging.info(f"Processed insurance list for patient {patient_id}: {insurance_list}")
        cache.set(cache_key, insurance_list, 3600) # Cache for 1 hour
        return JsonResponse(insurance_list, safe=False)
    except Exception as e:
        logging.error(f"Error fetching patient insurances for patient {patient_id}: {e}")
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
            # Get patient details to store their name
            patient_details_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id}/patients/{patient.original_id}"
            response = requests.get(patient_details_url, headers={"Authorization": f"Bearer {token}"})
            response.raise_for_status()
            patient_data = response.json()[0]
            patient.first_name = patient_data.get("firstname")
            patient.last_name = patient_data.get("lastname")
            patient.save()

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
                    athena_document_id=auth.get('referralauthid'),
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
                "scope": "athena/service/Athenanet.MDP.*",
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]
    except requests.RequestException as e:
        ImportLog.objects.create(task_name=task_name, last_run_at=current_run_time, status="failed", notes=f"Token Error: {e}")
        yield f"Failed to obtain OAuth token: {e}"
        return

    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch appointment cancellation reasons for 'no-show' mapping
    noshow_reason_ids = set()
    try:
        cancel_reasons_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id_arg}/appointmentcancelreasons"
        response = requests.get(cancel_reasons_url, headers=headers)
        response.raise_for_status()
        cancel_reasons_data = response.json()
        cancel_reasons = cancel_reasons_data.get('appointmentcancelreasons', [])
        for reason in cancel_reasons:
            if reason.get('noshow'):
                noshow_reason_ids.add(str(reason.get('appointmentcancelreasonid')))
        yield f"Found {len(noshow_reason_ids)} 'no-show' cancellation reason IDs."
    except requests.RequestException as e:
        yield f"Failed to fetch appointment cancel reasons: {e}"

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
    updated_count = 0
    for appt_summary in all_appointments:
        appointment_id = str(appt_summary.get("appointmentid"))
        if not appointment_id:
            continue

        try:
            # Get detailed appointment data
            appt_detail_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id_arg}/appointments/{appointment_id}"
            response = requests.get(appt_detail_url, headers=headers)
            response.raise_for_status()
            appt = response.json()[0]

            patient_id = str(appt.get("patientid"))
            provider_id = str(appt.get("providerid"))

            if not patient_id or not provider_id:
                continue

            # Get patient details to store their name
            patient_details_url = f"https://api.preview.platform.athenahealth.com/v1/{practice_id_arg}/patients/{patient_id}"
            response = requests.get(patient_details_url, headers=headers)
            response.raise_for_status()
            patient_data = response.json()[0]
            yield f"  -> Patient data from API: {patient_data}"

            patient, created = Patient.objects.get_or_create(
                original_id=patient_id,
            )
            if created:
                patient.save()  # Ensure pseudonym is created

            patient.first_name = patient_data.get("firstname")
            patient.last_name = patient_data.get("lastname")
            patient.save()

            provider, _ = Provider.objects.get_or_create(
                npi=provider_id, defaults={"full_name": f"Provider {provider_id}"}
            )

            ref_date_str = appt.get("date")
            if ref_date_str:
                ref_date = datetime.strptime(ref_date_str, "%m/%d/%Y").date()
            else:
                ref_date = timezone.now().date()

            # Determine Status
            status = Referral.Status.SCHEDULED
            if appt.get('replacementappointmentid'):
                status = Referral.Status.RESCHEDULED
            elif appt.get('appointmentstatus') == 'x':  # Cancelled
                cancel_reason_id = str(appt.get('appointmentcancellationreasonid'))
                if cancel_reason_id in noshow_reason_ids:
                    status = Referral.Status.NO_SHOW
                else:
                    status = Referral.Status.CANCELLED
            elif appt.get('appointmentstatus') in ['2', '3', '4']:  # Checked-in, Checked-out, Charge Entered
                status = Referral.Status.COMPLETED

            _, created = Referral.objects.update_or_create(
                athena_document_id=appointment_id,
                defaults={
                    "patient": patient,
                    "provider": provider,
                    "referral_date": ref_date,
                    "specialty": provider.specialty,
                    "status": status,
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1
        except requests.RequestException as e:
            yield f"Could not process appointment {appointment_id}: {e}"
            continue
    
    ImportLog.objects.update_or_create(
        task_name=task_name,
        defaults={
            "last_run_at": current_run_time,
            "status": "success",
            "notes": f"Created {created_count} and updated {updated_count} referrals."
        }
    )
    yield f"Import complete. Created {created_count} and updated {updated_count} referrals."

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

            ack_at_str = auth.get("acknowledged_at")
            if ack_at_str:
                referral_to_update.ack_at = datetime.strptime(ack_at_str, "%Y-%m-%dT%H:%M:%SZ")
                # If acknowledged_at is present, set status to ACKNOWLEDGED,
                # but don't downgrade if it's already a more advanced status.
                if status in [Referral.Status.PENDING, Referral.Status.SENT]:
                    status = Referral.Status.ACKNOWLEDGED
            else:
                referral_to_update.ack_at = None

            referral_to_update.status = status

            # Fetch patient encounters to get visit summary
            visit_summary_text = ""
            try:
                encounters_data = get(f"patients/{patient.original_id}/encounters", practice_id_arg, token)
                if encounters_data and encounters_data.get('encounters'):
                    # Sort encounters by date to find the most recent relevant one
                    sorted_encounters = sorted(encounters_data['encounters'], key=lambda x: datetime.strptime(x['encounterdate'], '%m/%d/%Y'), reverse=True)

                    # Try to find an encounter close to the referral date or scheduled date
                    target_date = referral_to_update.scheduled_at.date() if referral_to_update.scheduled_at else referral_to_update.referral_date
                    
                    best_encounter = None
                    min_date_diff = timedelta(days=365 * 100) # A very large difference

                    for enc in sorted_encounters:
                        enc_date = datetime.strptime(enc['encounterdate'], '%m/%d/%Y').date()
                        date_diff = abs(target_date - enc_date)
                        if date_diff < min_date_diff:
                            min_date_diff = date_diff
                            best_encounter = enc
                        # If we find an exact match, we can stop
                        if date_diff == timedelta(days=0):
                            break
                    
                    if best_encounter:
                        # Construct a simple summary from the best matching encounter
                        summary_parts = []
                        if best_encounter.get('encountertype'):
                            summary_parts.append(f"Type: {best_encounter['encountertype']}")
                        if best_encounter.get('encounterdate'):
                            summary_parts.append(f"Date: {best_encounter['encounterdate']}")
                        if best_encounter.get('reasonforvisit'):
                            summary_parts.append(f"Reason: {best_encounter['reasonforvisit']}")
                        if best_encounter.get('diagnoses'):
                            diag_names = [d.get('name') for d in best_encounter['diagnoses'] if d.get('name')]
                            if diag_names:
                                summary_parts.append(f"Diagnoses: {', '.join(diag_names)}")
                        
                        visit_summary_text = "; ".join(summary_parts)
                        if not visit_summary_text: # Fallback if no specific parts found
                            visit_summary_text = f"Encounter ID: {best_encounter.get('encounterid')}, Date: {best_encounter.get('encounterdate')}"

            except Exception as e:
                yield f"API error fetching encounters for patient {patient.original_id}: {e}. Skipping visit summary."
            
            referral_to_update.visit_summary = visit_summary_text

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


@login_required
def get_referral_details_ajax(request, pk):
    try:
        referral = get_object_or_404(Referral, pk=pk)
        user_practice = request.user.userprofile.practice
        if not user_practice or not user_practice.athena_practice_id:
            return JsonResponse({'error': 'User has no practice ID configured.'}, status=400)
        practice_id = user_practice.athena_practice_id
        
        encounter_id = referral.athena_encounter_id
        order_id = referral.athena_document_id

        if not encounter_id or not order_id:
            return JsonResponse({'error': 'Referral is missing the Athena encounter or order ID.'}, status=400)

        token = get_token()
        
        request_url = f"chart/encounter/{encounter_id}/orders/{order_id}"
        logging.info(f"Making direct Athena API call to: {request_url}")
        
        try:
            order_details = get(request_url, practice_id, token)
            logging.info(f"Received successful response from Athena API: {order_details}")
            
            if order_details and isinstance(order_details, list):
                return JsonResponse(order_details[0])
            elif order_details:
                return JsonResponse(order_details)
            else:
                return JsonResponse({'error': f'No details found for Order ID {order_id} in encounter {encounter_id}.'}, status=404)
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"Athena API HTTP Error ({http_err.response.status_code}): {http_err.response.text}", exc_info=True)
            return JsonResponse({'error': f"Athena API returned an error: {http_err.response.text}"}, status=http_err.response.status_code)
        except Exception as api_err:
            logging.error(f"Error during Athena API call: {api_err}", exc_info=True)
            return JsonResponse({'error': 'Failed to communicate with Athena API.'}, status=500)

    except Exception as e:
        logging.error(f"A critical error occurred in get_referral_details_ajax: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)

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
    try:
        user_practice = request.user.userprofile.practice
    except (UserProfile.DoesNotExist, AttributeError):
        user_practice = None

    if user_practice:
        referrals_qs = Referral.objects.filter(provider__practice=user_practice)
    else:
        referrals_qs = Referral.objects.all()

    query = request.GET.get('q', '').strip()
    if query:
        referrals_qs = referrals_qs.annotate(
            patient_full_name=Concat('patient__first_name', Value(' '), 'patient__last_name')
        ).filter(
            Q(patient__original_id__icontains=query) |
            Q(patient__pseudonym__icontains=query) |
            Q(patient_full_name__icontains=query) |
            Q(provider__full_name__icontains=query) |
            Q(specialty__icontains=query) |
            Q(status__icontains=query)
        )

    referrals = referrals_qs.order_by('-referral_date')

    data = []
    for referral in referrals:
        data.append({
            'pk': referral.pk,
            'patient_str': str(referral.patient),
            'provider_str': str(referral.provider) if referral.provider else 'N/A',
            'specialty': referral.specialty,
            'referral_date': referral.referral_date.strftime('%Y-%m-%d'),
            'status_val': referral.status,
            'status_display': referral.get_status_display(),
            'in_network': referral.in_network,
            'detail_url': reverse('referral_detail', args=[referral.pk]),
        })

    return JsonResponse(data, safe=False)
