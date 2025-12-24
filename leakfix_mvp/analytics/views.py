import requests
import difflib
from urllib.parse import urlencode
import time
import hashlib
import concurrent.futures
import collections
import os
from datetime import datetime
from threading import Lock
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Sum, Q, Avg, Value
from django.db.models.functions import Concat
from django.utils import timezone
from statistics import median
from datetime import timedelta
from decimal import Decimal
from .models import (
    Referral,
    Provider,
    Patient,
    Payer,
    ReferralHistory,
    Invoice,
    UserProfile,
    Practice,
    CPTCodeMapping,
    Department,
)
from .forms import ReferralForm
from analytics.ai_utils import generate_suggestions
import logging

# --- KPI dashboard ---
@login_required
def dashboard(request):
    if request.user.is_superuser:
        base_referrals = Referral.objects.all()
    else:
        try:
            user_practice = request.user.userprofile.practice
            if user_practice:
                base_referrals = Referral.objects.filter(practice=user_practice)
            else:
                base_referrals = Referral.objects.none()
        except (UserProfile.DoesNotExist, AttributeError):
            base_referrals = Referral.objects.none()

    # --- Quarter Filtering Logic ---
    selected_quarters = request.GET.getlist('quarter')
    current_year = timezone.now().year
    
    q_filters = Q()
    if selected_quarters:
        for q in selected_quarters:
            if q == '1': # Q1: Jan 1 - Mar 31
                q_filters |= Q(referral_date__gte=datetime(current_year, 1, 1), referral_date__lte=datetime(current_year, 3, 31))
            elif q == '2': # Q2: Apr 1 - Jun 30
                q_filters |= Q(referral_date__gte=datetime(current_year, 4, 1), referral_date__lte=datetime(current_year, 6, 30))
            elif q == '3': # Q3: Jul 1 - Sep 30
                q_filters |= Q(referral_date__gte=datetime(current_year, 7, 1), referral_date__lte=datetime(current_year, 9, 30))
            elif q == '4': # Q4: Oct 1 - Dec 31
                q_filters |= Q(referral_date__gte=datetime(current_year, 10, 1), referral_date__lte=datetime(current_year, 12, 31))
        
        referrals_in_period = base_referrals.filter(q_filters)
    else:
        referrals_in_period = base_referrals
    # --- End Quarter Filtering Logic ---

    referrals_with_provider_in_period = referrals_in_period.filter(provider__isnull=False)
    
    total = referrals_in_period.count()
    in_practice_network = referrals_with_provider_in_period.filter(is_in_practice_network=True).count()
    out_practice_network = referrals_with_provider_in_period.filter(is_in_practice_network=False).count()
    durations_sched = [
        (ref.scheduled_at.date() - ref.referral_date).days
        for ref in referrals_in_period.filter(scheduled_at__isnull=False)
    ]

    total_with_provider = referrals_in_period.filter(provider__isnull=False).count()
    in_practice_network_rate = (in_practice_network / total_with_provider * 100.0) if total_with_provider else 0
    out_practice_network_rate = (out_practice_network / total_with_provider * 100.0) if total_with_provider else 0
    
    out_of_practice_network_referrals_with_provider = referrals_in_period.filter(is_in_practice_network=False, provider__isnull=False)
    total_leakage_cost = out_of_practice_network_referrals_with_provider.aggregate(total_cost=Sum('rvu_cost'))['total_cost'] or Decimal('0.00')
    average_leakage_cost = (total_leakage_cost / out_of_practice_network_referrals_with_provider.count()) if out_of_practice_network_referrals_with_provider.count() > 0 else Decimal('0.00')


    completed = referrals_in_period.filter(status__in=[Referral.Status.COMPLETED, Referral.Status.CLOSED]).count()
    completion_rate = (completed / total * 100.0) if total else 0

    query_params = request.GET.copy()
    download_pdf_url = reverse('analytics:generate_quarterly_report') + '?' + query_params.urlencode() + '&format=pdf'
    download_csv_url = reverse('analytics:generate_quarterly_report') + '?' + query_params.urlencode() + '&format=csv'

    context = {
        'total': total,
        'in_practice_network': in_practice_network,
        'out_practice_network': out_practice_network,
        'in_practice_network_rate': in_practice_network_rate,
        'out_practice_network_rate': out_practice_network_rate,
        'completion_rate': completion_rate,
        'total_leakage_cost': total_leakage_cost,
        'average_leakage_cost': average_leakage_cost,
        'selected_quarters': selected_quarters,
        'current_year': timezone.now().year,
        'current_month': timezone.now().month,
        'download_pdf_url': download_pdf_url,
        'download_csv_url': download_csv_url,
    }
    return render(request, 'analytics/dashboard.html', context)


import json
import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from django.db.models.functions import Coalesce

# --- Provider list ---
@login_required
def provider_list(request):
    if request.user.is_superuser:
        providers = list(Provider.objects.all())
    else:
        try:
            user_practice = request.user.userprofile.practice
            if user_practice:
                providers = list(Provider.objects.filter(practices=user_practice))
            else:
                providers = []
        except (UserProfile.DoesNotExist, AttributeError):
            providers = []

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

        # Use the is_in_practice_network field from the model
        provider.is_preferred = provider.is_in_practice_network

    # Sort: preferred (in-practice-network) providers first, then by completeness score
    providers.sort(key=lambda p: (p.is_preferred, p.completeness_score), reverse=True)

    return render(request, 'analytics/provider_list.html', {'providers': providers})


# --- Provider search ---
@login_required
def provider_search(request):
    query = request.GET.get('q', '').strip()

    if request.user.is_superuser:
        providers = Provider.objects.all()
    else:
        try:
            user_practice = request.user.userprofile.practice
            if user_practice:
                providers = Provider.objects.filter(practices=user_practice)
            else:
                providers = Provider.objects.none()
        except (UserProfile.DoesNotExist, AttributeError):
            providers = Provider.objects.none()

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

        # Use the is_in_practice_network field from the model
        provider.is_preferred = provider.is_in_practice_network

    # Sort: preferred (in-practice-network) providers first, then by completeness score
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
        in_practice_network_count = refs.filter(is_in_practice_network=True).count()
        completed = refs.filter(status__in=[Referral.Status.COMPLETED, Referral.Status.CLOSED]).count()
        metrics[provider.id] = {
            'in_practice_network_rate': in_practice_network_count / total,
            'completion_rate': completed / total,
        }
    return metrics


def get_suggested_providers(referral, max_results=3):
    if not referral.provider:
        return [] # Return an empty list if the referral has no provider

    candidates = Provider.objects.filter(
        specialty__iexact=referral.provider.specialty
    ).exclude(id=referral.provider.id)
    metrics = get_provider_metrics()
    scored = []
    for p in candidates:
        m = metrics.get(p.id, None)
        if m:
            score = (
                0.5 * m['in_practice_network_rate']
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
            # The in_practice_network status is now determined by the provider's own flag
            is_in_practice_network = provider.is_in_practice_network

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
                is_in_practice_network=provider.is_in_practice_network, # Set automatically from provider's flag
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
    if request.user.is_superuser:
        referrals = Referral.objects.all()
    else:
        try:
            user_practice = request.user.userprofile.practice
            if user_practice:
                referrals = Referral.objects.filter(practice=user_practice)
            else:
                referrals = Referral.objects.none()
        except (UserProfile.DoesNotExist, AttributeError):
            referrals = Referral.objects.none()

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


@login_required
def referral_detail(request, pk):
    if request.user.is_superuser:
        referral = get_object_or_404(Referral, pk=pk)
    else:
        try:
            user_practice = request.user.userprofile.practice
        except (UserProfile.DoesNotExist, AttributeError):
            # If a non-superuser has no practice, they can't see any referrals.
            return render(request, 'analytics/referral_detail.html', {'error': 'You are not associated with a practice.'})
            
        referral = get_object_or_404(Referral, pk=pk, practice=user_practice)

    return render(request, 'analytics/referral_detail.html', {'referral': referral})

@login_required
def referral_detail_api(request, pk):
    try:
        referral = get_object_or_404(Referral, pk=pk)
        try:
            user_practice = request.user.userprofile.practice
        except UserProfile.DoesNotExist:
            logging.error("UserProfile.DoesNotExist for user: %s", request.user.username)
            return JsonResponse({'error': 'User has no practice associated with their profile.'}, status=400)

        if not user_practice or not user_practice.athena_practice_id:
            logging.error("User %s has no practice or athena_practice_id.", request.user.username)
            return JsonResponse({'error': 'User has no practice ID configured.'}, status=400)
        practice_id = user_practice.athena_practice_id
        
        encounter_id = referral.athena_encounter_id
        order_id = referral.athena_document_id

        if not encounter_id or not order_id:
            logging.error("Referral %s is missing Athena encounter or order ID.", pk)
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


@login_required
def set_referral_status(request, pk, state):
    if request.user.is_superuser:
        referral = get_object_or_404(Referral, pk=pk)
    else:
        try:
            user_practice = request.user.userprofile.practice
        except (UserProfile.DoesNotExist, AttributeError):
            return redirect('analytics:dashboard') 
            
        referral = get_object_or_404(Referral, pk=pk, practice=user_practice)

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
# def invoice_list(request):
#     invoices = Invoice.objects.order_by('-period_start')
#     return render(request, 'analytics/invoice_list.html', {'invoices': invoices})


# def invoice_detail(request, pk):
#     invoice = get_object_or_404(Invoice, pk=pk)
#     return render(request, 'analytics/invoice_detail.html', {'invoice': invoice})


# --- Metric detail view (unchanged from previous step) ---
@login_required
def metric_detail(request, metric):
    if request.user.is_superuser:
        base_referrals = Referral.objects.all()
    else:
        try:
            user_practice = request.user.userprofile.practice
            if user_practice:
                base_referrals = Referral.objects.filter(practice=user_practice)
            else:
                base_referrals = Referral.objects.none()
        except (UserProfile.DoesNotExist, AttributeError):
            base_referrals = Referral.objects.none()

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
        month_refs = base_referrals.filter(created_at__gte=month_start, created_at__lt=month_end)

        if metric == 'in_network_rate':
            title = "In-Practice-Network Rate"
            total = month_refs.count()
            in_net = month_refs.filter(is_in_practice_network=True).count()
            value = (Decimal(in_net) / Decimal(total) * 100) if total else Decimal('0')
        elif metric == 'out_of_network_rate':
            title = "Out-of-Practice-Network Rate"
            total = month_refs.count()
            out_net = month_refs.filter(is_in_practice_network=False).count()
            value = (Decimal(out_net) / Decimal(total) * 100) if total else Decimal('0')
        elif metric == 'completion_rate':
            title = "Completion Rate"
            total = month_refs.count()
            completed = month_refs.filter(status__in=[Referral.Status.COMPLETED, Referral.Status.CLOSED]).count()
            value = (Decimal(completed) / Decimal(total) * 100) if total else Decimal('0')
        elif metric in ['leakage_cost', 'total_leakage_cost']:
            title = "Total Leakage Cost"
            value = month_refs.filter(is_in_practice_network=False).aggregate(total_leak=Sum('rvu_cost')).get('total_leak') or Decimal('0')
        elif metric == 'retained_revenue':
            title = "Retained Revenue"
            avg_in_cost = month_refs.filter(is_in_practice_network=True).aggregate(avg=Avg('rvu_cost'))['avg'] or Decimal('0')
            in_net_count = month_refs.filter(is_in_practice_network=True).count()
            value = avg_in_cost * in_net_count
        elif metric == 'referral_volume':
            title = "Referral Volume"
            value = Decimal(month_refs.count())
        elif metric in ['avg_leakage_cost', 'average_leakage_cost']:
            title = "Average Leakage Cost"
            out_count = month_refs.filter(is_in_practice_network=False).count()
            total_leak = month_refs.filter(is_in_practice_network=False).aggregate(total_leak=Sum('rvu_cost')).get('total_leak') or Decimal('0')
            value = (total_leak / out_count) if out_count else Decimal('0')
        else:
            title = "Unknown Metric"
            value = Decimal('0')

        values.append(value)

    # Summary stats
    avg_value = (sum(values) / len(values)) if values else Decimal('0')
    max_value = max(values) if values else Decimal('0')
    min_value = min(values) if values else Decimal('0')
    latest_value = values[-1] if values else Decimal('0')

    # Simple trend calculation: compare last value to average
    if latest_value > avg_value * Decimal('1.05'):
        trend = "increasing"
    elif latest_value < avg_value * Decimal('0.95'):
        trend = "decreasing"
    else:
        trend = "flat"

    # Call the AI suggestion function
    try:
        suggestion_text = generate_suggestions(metric, latest_value, avg_value, trend)
    except Exception as e:
        suggestion_text = f"(AI suggestion unavailable: {e})"

    context = {
        'metric': title,
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
@login_required
def specialty_dashboard(request):
    """
    Compute metrics for each provider specialty.  This allows clinics
    to compare leakage and completion metrics across specialties.
    """
    if request.user.is_superuser:
        base_referrals = Referral.objects.all()
        providers = Provider.objects.all()
    else:
        try:
            user_practice = request.user.userprofile.practice
            if user_practice:
                base_referrals = Referral.objects.filter(practice=user_practice)
                providers = Provider.objects.filter(practices=user_practice)
            else:
                base_referrals = Referral.objects.none()
                providers = Provider.objects.none()
        except (UserProfile.DoesNotExist, AttributeError):
            base_referrals = Referral.objects.none()
            providers = Provider.objects.none()

    specialties = providers.values_list('specialty', flat=True).distinct()
    specialty_data = []
    for spec in specialties:
        if spec is None:
            continue
        
        refs = base_referrals.filter(provider__specialty=spec)
        total = refs.count()

        in_practice_network = refs.filter(is_in_practice_network=True).count()
        out_practice_network = refs.filter(is_in_practice_network=False).count()
        
        leakage_cost = refs.filter(is_in_practice_network=False).aggregate(total_leak=Sum('rvu_cost')).get('total_leak') or 0
        avg_leakage_cost = (leakage_cost / out_practice_network) if out_practice_network else 0
        
        avg_in_cost_agg = refs.filter(is_in_practice_network=True).aggregate(avg=Avg('rvu_cost'))
        avg_in_cost = avg_in_cost_agg['avg'] or 0

        retained_revenue = in_practice_network * avg_in_cost
        in_practice_network_rate = (in_practice_network / total * 100.0) if total else 0
        
        completed = refs.filter(status__in=[Referral.Status.COMPLETED, Referral.Status.CLOSED]).count()
        completion_rate = (completed / total * 100.0) if total else 0
        
        specialty_data.append({
            'specialty': spec,
            'total': total,
            'in_practice_network': in_practice_network,
            'out_practice_network': out_practice_network,
            'in_practice_network_rate': in_practice_network_rate,
            'completion_rate': completion_rate,
            'leakage_cost': leakage_cost,
            'avg_leakage_cost': avg_leakage_cost,
            'retained_revenue': retained_revenue,
        })
    return render(request, 'analytics/specialty_dashboard.html', {'specialty_data': specialty_data})


@login_required
def specialty_detail(request, specialty):
    """
    Compute metrics for a single provider specialty.
    """
    if request.user.is_superuser:
        base_referrals = Referral.objects.all()
    else:
        try:
            user_practice = request.user.userprofile.practice
            if user_practice:
                base_referrals = Referral.objects.filter(practice=user_practice)
            else:
                base_referrals = Referral.objects.none()
        except (UserProfile.DoesNotExist, AttributeError):
            base_referrals = Referral.objects.none()

    refs = base_referrals.filter(provider__specialty=specialty)
    total = refs.count()
    if specialty == 'None':
        in_practice_network = 0
        out_practice_network = 0
    else:
        in_practice_network = refs.filter(is_in_practice_network=True).count()
        out_practice_network = refs.filter(is_in_practice_network=False).count()
    leakage_cost = refs.filter(is_in_practice_network=False).aggregate(total_leak=Sum('rvu_cost')).get('total_leak') or 0
    avg_leakage_cost = (leakage_cost / out_practice_network) if out_practice_network else 0
    
    avg_in_cost_agg = refs.filter(is_in_practice_network=True).aggregate(avg=Avg('rvu_cost'))
    avg_in_cost = avg_in_cost_agg['avg'] or 0

    retained_revenue = in_practice_network * avg_in_cost
    in_practice_network_rate = (in_practice_network / total * 100.0) if total else 0
    completed = refs.filter(status__in=[Referral.Status.COMPLETED, Referral.Status.CLOSED]).count()
    completion_rate = (completed / total * 100.0) if total else 0

    context = {
        'specialty': specialty,
        'total': total,
        'in_practice_network': in_practice_network,
        'out_practice_network': out_practice_network,
        'in_practice_network_rate': in_practice_network_rate,
        'completion_rate': completion_rate,
        'leakage_cost': leakage_cost,
        'avg_leakage_cost': avg_leakage_cost,
        'retained_revenue': retained_revenue,
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
    
    if request.user.is_superuser:
        all_providers_qs = Provider.objects.all()
    else:
        try:
            user_practice = request.user.userprofile.practice
            if user_practice:
                all_providers_qs = Provider.objects.filter(practices=user_practice)
            else:
                all_providers_qs = Provider.objects.none()
        except (UserProfile.DoesNotExist, AttributeError):
            all_providers_qs = Provider.objects.none()

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
            provider = Provider.objects.get(providerid=providerid, practices=user_practice)
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
            provider_id = data['provider_id']
            provider = Provider.objects.get(providerid=provider_id, practices=user_practice)
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
                is_in_practice_network=provider.is_in_practice_network,
                is_urgent=data.get('is_urgent', False),
                status=status,
                referral_date=datetime.now().date(),
                documenttypeid=order_type_id,
                athena_document_id=athena_document_id, # Storing the order/document ID
                athena_encounter_id=encounter_id, # Storing the encounter ID
                provider_note=provider_note,
                note_to_patient=note_to_patient,
            )

            # Calculate RVU cost on the spot
            rvu_calculated_cost = Decimal("0.00")
            logging.info(f"--- RVU Calculation for new referral (ordertypeid: {order_type_id}) ---")
            if order_type_id:
                try:
                    cpt_mapping = CPTCodeMapping.objects.get(ordertypeid=order_type_id)
                    logging.info(f"Found CPTCodeMapping: {cpt_mapping.cpt_code}")
                    practice = user_practice
                    if practice and practice.work_gpci and practice.pe_gpci and practice.mp_gpci and practice.conversion_factor:
                        logging.info(f"Practice GPCI/CF values: wGPCI={practice.work_gpci}, peGPCI={practice.pe_gpci}, mpGPCI={practice.mp_gpci}, CF={practice.conversion_factor}")
                        logging.info(f"RVU components: wRVU={cpt_mapping.work_rvu}, peRVU={cpt_mapping.non_fac_pe_rvu}, mpRVU={cpt_mapping.mp_rvu}")
                        total_rvu = (cpt_mapping.work_rvu * practice.work_gpci) + \
                                    (cpt_mapping.non_fac_pe_rvu * practice.pe_gpci) + \
                                    (cpt_mapping.mp_rvu * practice.mp_gpci)
                        logging.info(f"Calculated Total RVU: {total_rvu}")
                        rvu_calculated_cost = total_rvu * practice.conversion_factor
                        logging.info(f"Final Calculated RVU Cost: {rvu_calculated_cost}")
                    else:
                        logging.warning(f"Practice '{practice.name}' is missing GPCI or Conversion Factor values. Cannot calculate RVU cost.")
                except CPTCodeMapping.DoesNotExist:
                    logging.info(f"No CPTCodeMapping found for ordertypeid {order_type_id}")
                except Exception as e:
                    logging.error(f"Error calculating RVU cost for ordertypeid {order_type_id}: {e}")
            else:
                logging.info("No ordertypeid provided. Cannot calculate RVU cost.")
            logging.info("--- End RVU Calculation ---")

            referral.rvu_cost = rvu_calculated_cost
            referral.practice = user_practice
            referral.save()
            
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
import csv
import io

from . import athena_client
from .forms import CPTCodeMappingUploadForm
from .models import CPTCodeMapping


from django.http import StreamingHttpResponse

# Helper functions for Athena sync

@login_required
@user_passes_test(lambda u: u.is_superuser)
def management(request):
    upload_form = CPTCodeMappingUploadForm()
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
            return redirect('analytics:management')
        
        if 'upload_cpt_mappings' in request.POST:
            upload_form = CPTCodeMappingUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                csv_file = request.FILES['file']
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, 'This is not a CSV file.')
                else:
                    try:
                        decoded_file = csv_file.read().decode('utf-8')
                        io_string = io.StringIO(decoded_file)
                        reader = csv.reader(io_string)
                        next(reader) # Skip header row
                        for row in reader:
                            # ordertypeid,name,cpt_code,work_rvu,non_fac_pe_rvu,fac_pe_rvu,mp_rvu
                            _, created = CPTCodeMapping.objects.update_or_create(
                                ordertypeid=row[0],
                                defaults={
                                    'name': row[1],
                                    'cpt_code': row[2],
                                    'work_rvu': Decimal(row[3]),
                                    'non_fac_pe_rvu': Decimal(row[4]),
                                    'fac_pe_rvu': Decimal(row[5]),
                                    'mp_rvu': Decimal(row[6]),
                                }
                            )
                        messages.success(request, 'CPT Code Mappings uploaded successfully.')
                    except Exception as e:
                        messages.error(request, f'Error processing file: {e}')

                return redirect('analytics:management')

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
        return redirect('analytics:management')

    # Handle Update GPCI & CF Form
    if 'update_gpci_cf' in request.POST:
        practice_id = request.POST.get('practice_id')
        work_gpci_str = request.POST.get('work_gpci')
        pe_gpci_str = request.POST.get('pe_gpci')
        mp_gpci_str = request.POST.get('mp_gpci')
        conversion_factor_str = request.POST.get('conversion_factor')

        if practice_id and work_gpci_str and pe_gpci_str and mp_gpci_str and conversion_factor_str:
            try:
                practice = Practice.objects.get(id=practice_id)
                practice.work_gpci = Decimal(work_gpci_str)
                practice.pe_gpci = Decimal(pe_gpci_str)
                practice.mp_gpci = Decimal(mp_gpci_str)
                practice.conversion_factor = Decimal(conversion_factor_str)
                practice.save()
                messages.success(request, f"GPCI and Conversion Factor updated for {practice.name}.")
            except Practice.DoesNotExist:
                messages.error(request, "Practice not found.")
            except ValueError:
                messages.error(request, "Invalid number format for GPCI or Conversion Factor.")
        else:
            messages.error(request, 'All fields are required to update GPCI and Conversion Factor.')
        return redirect('analytics:management')
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
        return redirect('analytics:management')

    practices = Practice.objects.all()
    return render(request, 'analytics/management.html', {'practices': practices, 'upload_form': upload_form})





@login_required
@user_passes_test(lambda u: u.is_superuser)
def stream_command_view(request):
    command_name = request.GET.get('command')
    practice_id = request.GET.get('practice_id')
    client_id = request.GET.get('client_id')
    client_secret = request.GET.get('client_secret')

    def event_stream():
        # Common setup for all sync commands
        def sync_setup(practice_id, client_id, client_secret):
            try:
                practice = Practice.objects.get(id=practice_id)
                athena_practice_id = practice.athena_practice_id
            except Practice.DoesNotExist:
                yield f"event: error\ndata: Practice with ID {practice_id} not found.\n\n"
                return None, None, None, None
            
            token = get_token()
            if not token:
                yield f"event: error\ndata: Failed to obtain Athena API token.\n\n"
                return None, None, None, None
            
            headers = {"Authorization": f"Bearer {token}"}
            return practice, athena_practice_id, token, headers

        if command_name == 'run_full_sync':
            log_dir = "/home/user/.gemini/tmp/8f5f700a5a9f69e45277c43d3d10c30291760b8bf9e6feaa90db45dfd7fe33da"
            log_filename = datetime.now().strftime("sync_log_%Y%m%d_%H%M%S.txt")
            log_filepath = os.path.join(log_dir, log_filename)
            
            try:
                with open(log_filepath, 'w') as f:
                    f.write(f"--- Starting Athena sync for practice ID {practice_id} ---\n")
                    yield f"event: message\ndata: Logs will also be saved to: {log_filepath}\n\n"
                    yield f"event: message\ndata: Starting full Athena sync for practice ID {practice_id}...\n\n"
                    f.write(f"Starting full Athena sync for practice ID {practice_id}...\n")

                    for message in run_full_athena_sync(practice_id, client_id, client_secret, debug_file=f):
                        f.write(message + '\n')
                        yield f"event: message\ndata: {message}\n\n"
                    
                    f.write(f"--- Sync process finished ---\n")
                    yield "event: close\ndata: Sync process finished.\n\n"
            except Exception as file_error:
                yield f"event: error\ndata: Error writing log file: {file_error}\n\n"
                yield f"event: message\ndata: Starting full Athena sync for practice ID {practice_id} (without log file)...\n\n"
                for message in run_full_athena_sync(practice_id, client_id, client_secret):
                    yield f"event: message\ndata: {message}\n\n"
                yield "event: close\ndata: Sync process finished.\n\n"

        elif command_name in ['sync_departments', 'sync_providers', 'sync_patients', 'sync_referrals']:
            practice, athena_practice_id, token, headers = yield from sync_setup(practice_id, client_id, client_secret)
            if not practice:
                return

            if command_name == 'sync_departments':
                yield f"event: message\ndata: Starting department sync for practice ID {practice_id}...\n\n"
                for message in _sync_departments(athena_practice_id, headers, None):
                    yield f"event: message\ndata: {message}\n\n"
            
            elif command_name == 'sync_providers':
                yield f"event: message\ndata: Starting provider sync for practice ID {practice_id}...\n\n"
                for message in _sync_providers(athena_practice_id, headers, practice, None):
                    yield f"event: message\ndata: {message}\n\n"

            elif command_name == 'sync_patients':
                yield f"event: message\ndata: Starting patient sync for practice ID {practice_id}...\n\n"
                department_ids = list(Department.objects.values_list('department_id', flat=True))
                if not department_ids:
                    yield f"event: error\ndata: No departments found in the database. Please run 'Sync Departments' first.\n\n"
                    yield "event: close\ndata: Sync process finished.\n\n"
                    return
                for message in _sync_patients(athena_practice_id, token, department_ids, None):
                    yield f"event: message\ndata: {message}\n\n"
            
            elif command_name == 'sync_referrals':
                yield f"event: message\ndata: Starting referral sync for practice ID {practice_id}...\n\n"
                for message in _sync_referrals(athena_practice_id, token, practice, None):
                    yield f"event: message\ndata: {message}\n\n"

            yield "event: close\ndata: Sync process finished.\n\n"

        else:
            yield f"event: error\ndata: Unknown or obsolete command: {command_name}.\n\n"
            yield "event: close\ndata: Sync process finished.\n\n"

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')
# --- Delete referral ---
@login_required
def delete_referral(request, pk):
    """
    Delete a referral by its primary key.  Redirect back to the dashboard.
    """
    if request.user.is_superuser:
        referral = get_object_or_404(Referral, pk=pk)
    else:
        try:
            user_practice = request.user.userprofile.practice
        except (UserProfile.DoesNotExist, AttributeError):
            # If a non-superuser has no practice, they can't delete any referrals.
            return redirect('analytics:dashboard') # Or show an error
            
        referral = get_object_or_404(Referral, pk=pk, practice=user_practice)

    referral.delete()
    return redirect('analytics:dashboard')


@login_required
def get_referral_details_ajax(request, pk):
    try:
        referral = get_object_or_404(Referral, pk=pk)
        try:
            user_practice = request.user.userprofile.practice
        except UserProfile.DoesNotExist:
            logging.error("UserProfile.DoesNotExist for user: %s", request.user.username)
            return JsonResponse({'error': 'User has no practice associated with their profile.'}, status=400)

        if not user_practice or not user_practice.athena_practice_id:
            logging.error("User %s has no practice or athena_practice_id.", request.user.username)
            return JsonResponse({'error': 'User has no practice ID configured.'}, status=400)
        practice_id = user_practice.athena_practice_id
        
        encounter_id = referral.athena_encounter_id
        order_id = referral.athena_document_id

        if not encounter_id or not order_id:
            logging.error("Referral %s is missing Athena encounter or order ID.", pk)
            return JsonResponse({'error': 'Referral is missing the Athena encounter or order ID.'}, status=400)

        token = get_token()
        
        request_url = f"chart/encounter/{encounter_id}/orders/{order_id}"
        logging.info(f"Making direct Athena API call to: {request_url}")
        
        try:
            order_details = get(request_url, practice_id, token)
            logging.info(f"Received raw response from Athena API: {order_details}")
            
            if order_details and isinstance(order_details, list):
                # If the endpoint returns a list (even if it's a single item list)
                if order_details[0]: # Check if the list is not empty
                    logging.info(f"Returning JSON for order: {JsonResponse(order_details[0]).content.decode('utf-8')}")
                    return JsonResponse(order_details[0])
                else:
                    return JsonResponse({'error': f'Empty response from Athena for Order ID {order_id}.'}, status=404)
            elif order_details:
                # If the endpoint returns a single dictionary directly
                logging.info(f"Returning JSON for order: {JsonResponse(order_details).content.decode('utf-8')}")
                return JsonResponse(order_details)
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"Athena API HTTP Error ({http_err.response.status_code}): {http_err.response.text}", exc_info=True)
            return JsonResponse({'error': f"Athena API returned an error: {http_err.response.text}"}, status=http_err.response.status_code)
        except Exception as api_err:
            logging.error(f"Error during Athena API call: {api_err}", exc_info=True)
            return JsonResponse({'error': 'Failed to communicate with Athena API.'}, status=500)

    except Exception as e:
        logging.error(f"A critical error occurred in get_referral_details_ajax: {e}", exc_info=True)
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)


@login_required
@require_POST
def update_referral_status_ajax(request, pk):
    try:
        referral = get_object_or_404(Referral, pk=pk)
        new_status = request.POST.get('status')
        if new_status and new_status.lower() in Referral.Status.values:
            referral.status = new_status.lower()
            referral.save()
            ReferralHistory.objects.create(referral=referral, status=referral.status)
            return JsonResponse({'success': True, 'new_status': referral.get_status_display()})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def referral_detail(request, pk):
    referral = get_object_or_404(Referral, pk=pk)
    return render(request, 'analytics/referral_detail.html', {
        'referral': referral,
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
            'in_network': referral.in_network,
            'detail_url': reverse('referral_detail', args=[referral.pk]),
        })

    return JsonResponse(data, safe=False)

def _sync_departments(athena_practice_id, headers, debug_file):
    """Fetches all departments for a practice and stores them in the database."""
    department_ids = []
    yield "\nFetching all departments for practice..."
    if debug_file:
        debug_file.write("\nFetching all departments for practice...\n")
    try:
        departments_url = f"https://api.preview.platform.athenahealth.com/v1/{athena_practice_id}/departments?limit=1000"
        response = requests.get(departments_url, headers=headers)
        response.raise_for_status()
        departments_data = response.json().get("departments", [])
        
        # Clear existing departments to ensure a fresh sync
        Department.objects.all().delete()
        
        for d in departments_data:
            if "departmentid" in d:
                dep_id = str(d['departmentid'])
                Department.objects.get_or_create(department_id=dep_id)
                department_ids.append(dep_id)

        msg = f"  Synced {len(department_ids)} departments."
        yield msg
        if debug_file:
            debug_file.write(msg + "\n")
    except requests.RequestException as e:
        msg = f"ERROR: Could not fetch departments: {e}. Aborting."
        yield msg
        if debug_file:
            debug_file.write(msg + "\n")
        raise
    return department_ids

def _sync_providers(athena_practice_id, headers, practice, debug_file):
    """Fetches and syncs providers for a given practice."""
    yield "\nStep 2: Syncing Providers..."
    if debug_file:
        debug_file.write("\nStep 2: Syncing Providers...\n")
    try:
        provider_url = f"https://api.preview.platform.athenahealth.com/v1/{athena_practice_id}/providers?limit=1000"
        response = requests.get(provider_url, headers=headers)
        response.raise_for_status()
        providers_data = response.json().get("providers", [])

        created_count = 0
        updated_count = 0
        for provider_data in providers_data:
            provider_id = str(provider_data.get("providerid"))
            npi = provider_data.get("npi")

            if not provider_id:
                continue

            defaults = {
                'full_name': provider_data.get("displayname", ""),
                'specialty': provider_data.get("specialty", ""),
                'providerid': provider_id,
            }
            
            provider = None
            created = False

            if npi:
                # NPI is the source of truth for uniqueness.
                provider, created = Provider.objects.update_or_create(
                    npi=npi,
                    defaults=defaults
                )
            else:
                # No NPI. This provider can't be uniquely identified globally.
                # Try to find a provider with this providerid already linked to this practice.
                existing_providers = Provider.objects.filter(providerid=provider_id, practices=practice)
                if existing_providers.exists():
                    provider = existing_providers.first()
                    provider.full_name = defaults['full_name']
                    provider.specialty = defaults['specialty']
                    provider.save()
                    created = False
                    if existing_providers.count() > 1:
                        msg = f"WARNING: Found multiple providers with providerid {provider_id} for practice {practice.name}. Using the first one."
                        yield msg
                        if debug_file:
                            debug_file.write(msg + "\n")
                else:
                    # To be safe and avoid incorrect linking, we create a new provider record.
                    # This may lead to duplicates if the same no-NPI provider works at multiple synced practices.
                    provider = Provider.objects.create(**defaults)
                    created = True

            if provider:
                provider.practices.add(practice)
                if created:
                    created_count += 1
                else:
                    updated_count += 1
        msg = f"Synced providers. {created_count} new providers created, {updated_count} updated."
        yield msg
        if debug_file:
            debug_file.write(msg + "\n")
    except requests.RequestException as e:
        msg = f"ERROR during Provider Sync: {e}. Aborting."
        yield msg
        if debug_file:
            debug_file.write(msg + "\n")
        raise # Re-raise the exception so the caller can handle it
def _sync_patients(athena_practice_id, token, department_ids, debug_file):
    from .models import ImportLog, Patient
    task_name = "run_sync_patients"
    try:
        current_run_time = timezone.now()
        def _fetch_patients_for_department(dept_id, debug_file, token):
            """
            Fetches a list of patients for a given department. If the department is too large,
            it recursively breaks the query down using a series of partitioning fields.
            Returns a tuple: (list_of_patients, list_of_messages)
            """
            messages = []
            
            # Define the fields and their possible values for partitioning large queries
            partition_fields = [
                ('sex', ['M', 'F']),
                ('status', ['a', 'i', 'p', 'd']),
                ('maritalstatus', ['D', 'M', 'S', 'U', 'W', 'X', 'P']),
                ('veteran', ['Y', 'N', 'P']),
                ('agriculturalworker', ['Y', 'N', 'P']),
                ('schoolbasedhealthcenter', ['Y', 'N', 'P']),
                ('publichousing', ['Y', 'N', 'P']),
                ('contactrelationship', ['SPOUSE', 'PARENT', 'CHILD', 'SIBLING', 'FRIEND', 'COUSIN', 'GUARDIAN', 'OTHER']),
                ('nextkinrelationship', ['SPOUSE', 'PARENT', 'CHILD', 'SIBLING', 'FRIEND', 'COUSIN', 'GUARDIAN', 'OTHER']),
                ('contactpreference', ['HOMEPHONE', 'MAIL', 'MOBILEPHONE', 'PORTAL', 'WORKPHONE']),
                ('consenttotext', [True, False]),
                ('omitbalances', [True, False]),
                ('omitphotoinformation', [True, False]),
                ('omitdefaultpharmacy', [True, False]),
                ('consenttocall', [True, False]),
                ('homeboundyn', [True, False]),
                ('povertylevelincomerangedeclined', [True, False]),
                ('show2015edcehrtvalues', [True, False]),
            ]

            def _get_paginated_patients(params):
                """Helper to get all pages for a given query."""
                # This function remains the same, it just fetches all pages for a given set of params
                patients = []
                offset = 0
                limit = 1000
                while True:
                    paginated_params = params.copy()
                    paginated_params['limit'] = limit
                    paginated_params['offset'] = offset
                    
                    if debug_file:
                        debug_file.write(f"  Fetching patients with params: {paginated_params}\n")
                    
                    response = get("patients", athena_practice_id, token, params=paginated_params)
                    current_page = response.get("patients", [])
                    patients.extend(current_page)
                    
                    if len(current_page) < limit:
                        break
                    offset += limit
                return patients
            
            def get_recursively(base_params, field_index):
                """Recursively partition the search until the API call succeeds."""
                # Base case: If we've exhausted our partitioning fields, we cannot proceed.
                if field_index >= len(partition_fields):
                    err_msg = f"    ERROR: Cannot break down query further for params {base_params}. Some patients may be missed."
                    messages.append(err_msg)
                    if debug_file:
                        debug_file.write(err_msg + "\n")
                    return []
                field_name, values = partition_fields[field_index]
                partition_patients = []
                for value in values:
                    new_params = base_params.copy()
                    new_params[field_name] = value
                    
                    try:
                        # Try to fetch with the new, more refined query
                        patients = _get_paginated_patients(new_params)
                        partition_patients.extend(patients)
                        
                        msg = f"    Successfully fetched {len(patients)} patients for sub-query: {new_params}"
                        messages.append(msg)
                        if debug_file:
                            debug_file.write(msg + "\n")

                    except requests.exceptions.HTTPError as e:
                        # Check if this smaller chunk is *still* too large
                        is_too_large_error = False
                        try:
                            if "The given search parameters would produce a total data set larger than 1000 records" in e.response.text:
                                is_too_large_error = True
                        except (ValueError, AttributeError):
                            pass
                        
                        if is_too_large_error:
                            # If it's still too large, recurse to the next field
                            msg = f"    Chunk {new_params} is still too large. Recursing to next field..."
                            messages.append(msg)
                            if debug_file:
                                debug_file.write(msg + "\n")
                            partition_patients.extend(get_recursively(new_params, field_index + 1))
                        else:
                            # A different, unexpected HTTP error occurred
                            err_msg = f"    ERROR: HTTP error for sub-query {new_params}: {e}"
                            messages.append(err_msg)
                            if debug_file:
                                debug_file.write(err_msg + "\n")
                return partition_patients

            # --- Main logic for _fetch_patients_for_department ---
            try:
                # First, try a direct fetch. This will work for small departments.
                initial_params = {'departmentid': dept_id}
                all_patients = _get_paginated_patients(initial_params)
                return (all_patients, messages)
                
            except requests.exceptions.HTTPError as e:
                is_too_large_error = False
                try:
                    if "The given search parameters would produce a total data set larger than 1000 records" in e.response.text:
                        is_too_large_error = True
                except (ValueError, AttributeError):
                    pass

                if is_too_large_error:
                    msg = f"  Department {dept_id} is too large. Starting recursive breakdown..."
                    messages.append(msg)
                    if debug_file:
                        debug_file.write(msg + "\n")
                    
                    # Start the recursive breakdown process
                    all_patients = get_recursively({'departmentid': dept_id}, 0)
                    return (all_patients, messages)
                else:
                    # Re-raise any other, unexpected HTTP error
                    raise e
            except Exception as e:
                # Handle other unexpected errors
                raise e

        patients_created_count = 0
        patients_updated_count = 0
        synced_patient_ids = set()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            future_to_department = {
                executor.submit(_fetch_patients_for_department, dept_id, debug_file, token): dept_id
                for dept_id in department_ids
            }

            for future in concurrent.futures.as_completed(future_to_department):
                dept_id = future_to_department[future]
                
                try:
                    patients_in_dept, messages = future.result()
                    for msg in messages:
                        yield msg
                    
                    log_msg = f"  Finished fetching for department {dept_id}. Found {len(patients_in_dept)} patients."
                    logging.info(log_msg)
                    if debug_file:
                        debug_file.write(log_msg + "\n")

                except Exception as e:
                    yield f"  ERROR: A worker task for patients (dept:{dept_id}) failed: {e}"
                    continue

                if not patients_in_dept:
                    # This is normal for departments with no patients, no need to log verbosely
                    continue
                
                for patient_data in patients_in_dept:
                    athena_patient_id = str(patient_data.get("patientid"))
                    if not athena_patient_id or athena_patient_id in synced_patient_ids:
                        continue
                    
                    synced_patient_ids.add(athena_patient_id)
                    pseudonym_for_lookup = hashlib.sha256(athena_patient_id.encode()).hexdigest()

                    _, created = Patient.objects.update_or_create(
                        pseudonym=pseudonym_for_lookup,
                        defaults={
                            "original_id": athena_patient_id,
                        }
                    )
                    if created:
                        patients_created_count += 1
                    else:
                        patients_updated_count += 1
                
                total_synced = len(synced_patient_ids)
                if total_synced > 0 and total_synced % 1000 == 0: 
                    yield f"  Total unique patients synced so far: {total_synced} (New: {patients_created_count}, Updated: {patients_updated_count})"
        
        yield f"Synced patients. {patients_created_count} new patients created, {patients_updated_count} updated across {len(department_ids)} departments."
    except Exception as e:
        logging.error(f"Athena API Error (Patient Sync): {e}", exc_info=True)
        yield f"ERROR during Patient Sync: {e}. Check logs for details. Aborting."
        ImportLog.objects.update_or_create(task_name=task_name, defaults={"last_run_at": current_run_time, "status": "failed", "notes": f"Failed during patient sync: {e}"})
        return
def _sync_referrals(athena_practice_id, token, practice, debug_file):
    from .models import ImportLog, Patient, Provider, Referral, Department
    task_name = "run_sync_referrals"
    try:
        current_run_time = timezone.now()
        all_patients = Patient.objects.all()
        all_department_ids = list(Department.objects.values_list('department_id', flat=True))
        
        num_patients = all_patients.count()
        num_departments = len(all_department_ids)
        total_api_calls_estimate = num_patients * num_departments

        # --- Time Estimation ---
        if total_api_calls_estimate > 0:
            estimated_total_seconds = total_api_calls_estimate / 14 
            hours = int(estimated_total_seconds // 3600)
            minutes = int((estimated_total_seconds % 3600) // 60)
            yield f"  ESTIMATE: Submitting approximately {total_api_calls_estimate} API calls to the thread pool."
            yield f"  Estimated time with rate limiting: about {hours} hours and {minutes} minutes."
            yield "  This is a rough estimate and the actual time may vary."
        # --- End Time Estimation ---

        referrals_created_count = 0
        referrals_updated_count = 0
        skipped_count = 0
        processed_api_calls = 0
        
        practice_provider_ids = set(map(str, practice.provider_set.values_list('providerid', flat=True)))

        def _fetch_referrals_for_patient(patient, department_id, debug_file, token):
            """Worker to fetch orders for a patient for a specific department, respecting rate limits."""
            if debug_file:
                debug_file.write(f"Referral worker processing patient '{patient.original_id}' for department '{department_id}'\n")
            try:
                if(department_id == -1):
                    return (None, patient, None)
                params = {"limit": 250, "departmentid": department_id}
                orders_data = get(f"patients/{patient.original_id}/documents/order", athena_practice_id, token, params=params)
                return (orders_data, patient, None)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    logging.error(f"Rate limit exceeded for patient {patient.original_id}, dept {department_id}. Adjust rate limiter. Error: {e}")
                    return (None, patient, f"Rate Limit Error for Patient {patient.original_id}, Dept {department_id}: {e}")
                elif e.response.status_code == 400 and "The specified patient does not exist in that department." in e.response.text:
                    # This is an expected error if a patient is not associated with a specific department
                    logging.info(f"Patient {patient.original_id} does not exist in department {department_id} (expected).")
                    return (None, patient, None)
                else:
                    logging.error(f"Failed to sync referrals for patient {patient.original_id}, dept {department_id}: {e}")
                    return (None, patient, f"API Error for Patient {patient.original_id}, Dept {department_id}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred for patient {patient.original_id}, dept {department_id}: {e}")
                return (None, patient, f"Unexpected Error for Patient {patient.original_id}, Dept {department_id}: {e}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
            future_to_patient = {
                executor.submit(_fetch_referrals_for_patient, patient, dept_id, debug_file, token): patient
                for patient in all_patients
                for dept_id in all_department_ids
            }
            total_api_calls = len(future_to_patient)

            for future in concurrent.futures.as_completed(future_to_patient):
                processed_api_calls += 1
                if processed_api_calls % 100 == 0:
                    yield f"  Processed {processed_api_calls} of {total_api_calls} referral API calls..."

                patient = future_to_patient[future]
                result = future.result()
                if not isinstance(result, tuple) or len(result) != 3:
                    yield f"  --> UNEXPECTED WORKER RESULT for patient {patient.original_id}: Type={type(result)}, Value={result}"
                    continue
                
                orders_data, _, error = result

                if error:
                    yield f"  ERROR for patient {patient.original_id}: {error}"
                    continue
                if not orders_data or not orders_data.get("orders"):
                    continue

                for order in orders_data["orders"]:
                    # ... (rest of the processing logic remains the same)
                    if not (order.get('ordertype') == 'CONSULT' and 'referral' in order.get('documentdescription', '').lower()):
                        skipped_count += 1
                        continue

                    provider_id_from_order = order.get('providerid')
                    provider = None

                    if provider_id_from_order and str(provider_id_from_order) in practice_provider_ids:
                        try:
                            provider = Provider.objects.filter(providerid=str(provider_id_from_order), practices=practice).first()
                            if not provider:
                                skipped_count += 1
                                continue
                        except Provider.DoesNotExist:
                            skipped_count += 1
                            continue
                    else:
                        skipped_count += 1
                        continue
                    
                    referral_date_str = order.get('createddate')
                    referral_date = datetime.strptime(referral_date_str, '%m/%d/%Y').date() if referral_date_str else timezone.now().date()
                    
                    documenttypeid = order.get('documenttypeid')
                    rvu_calculated_cost = Decimal("0.00")
                    if documenttypeid:
                        try:
                            cpt_mapping = CPTCodeMapping.objects.get(ordertypeid=documenttypeid)
                            if practice.work_gpci and practice.pe_gpci and practice.mp_gpci and practice.conversion_factor:
                                total_rvu = (cpt_mapping.work_rvu * practice.work_gpci) + \
                                            (cpt_mapping.non_fac_pe_rvu * practice.pe_gpci) + \
                                            (cpt_mapping.mp_rvu * practice.mp_gpci)
                                rvu_calculated_cost = total_rvu * practice.conversion_factor
                        except CPTCodeMapping.DoesNotExist:
                            pass
                        except Exception as e:
                            logging.error(f"Error calculating RVU for order {order.get('orderid')}: {e}")

                    defaults = {
                        'patient': patient,
                        'is_in_practice_network': provider.is_in_practice_network if provider else False,
                        'rvu_cost': rvu_calculated_cost,
                        'practice': practice,
                    }
                    if provider: defaults['provider'] = provider
                    if referral_date: defaults['referral_date'] = referral_date
                    if provider and provider.specialty: defaults['specialty'] = provider.specialty
                    if order.get("status"): defaults['status'] = order.get("status").lower()
                    if order.get('encounterid'): defaults['athena_encounter_id'] = order.get('encounterid')
                    if documenttypeid: defaults['documenttypeid'] = documenttypeid

                    _, created = Referral.objects.update_or_create(
                        athena_document_id=order.get('orderid'),
                        defaults=defaults
                    )
                    if created:
                        referrals_created_count += 1
                    else:
                        referrals_updated_count += 1

        yield f"Synced referrals. Created: {referrals_created_count}, Updated: {referrals_updated_count}, Skipped: {skipped_count}."
    except Exception as e:
        logging.error(f"An unexpected error occurred during referral sync: {e}", exc_info=True)
        yield f"ERROR during Referral Sync: {e}. Aborting."
        ImportLog.objects.update_or_create(task_name=task_name, defaults={"last_run_at": current_run_time, "status": "failed", "notes": f"Failed during referral sync: {e}"})
        return
def run_full_athena_sync(practice_id_arg, client_id_arg, client_secret_arg, debug_file=None):
    """
    A comprehensive, unified sync function for a given practice.
    This function establishes a baseline of referral orders and then updates their
    status from the authoritative encounter context.
    """
    from .models import ImportLog, Practice, Patient, Provider, Referral
    
    task_name = "run_full_athena_sync"
    current_run_time = timezone.now()
    
    # --- Step 1: Initialization ---
    yield "Step 1: Initializing Sync Process..."
    try:
        practice = Practice.objects.get(id=practice_id_arg)
        athena_practice_id = practice.athena_practice_id
    except Practice.DoesNotExist:
        yield f"ERROR: Practice with local ID {practice_id_arg} not found. Aborting."
        return

    token = get_token()
    if not token:
        yield "ERROR: Failed to obtain Athena API token. Aborting sync."
        ImportLog.objects.update_or_create(task_name=task_name, defaults={"last_run_at": current_run_time, "status": "failed", "notes":"Failed to obtain token."})
        return
    yield "Token obtained successfully."
    headers = {"Authorization": f"Bearer {token}"}

    # --- Fetch Departments ---
    try:
        yield from _sync_departments(athena_practice_id, token, headers, debug_file)
    except Exception as e:
        # Handle the exception re-raised by _sync_departments
        ImportLog.objects.update_or_create(task_name=task_name, defaults={"last_run_at": current_run_time, "status": "failed", "notes": f"Failed to fetch departments: {e}"})
        return

    # --- Sync Providers ---
    try:
        yield from _sync_providers(athena_practice_id, token, headers, practice, debug_file)
    except Exception as e:
        ImportLog.objects.update_or_create(task_name=task_name, defaults={"last_run_at": current_run_time, "status": "failed", "notes": f"Failed during provider sync: {e}"})
        return
    # --- Step 3: Sync Patients (Concurrent with Rate Limiting) ---
    yield "\nStep 3: Syncing Patients (using concurrency and rate limiting)..."
    try:
        yield from _sync_patients(athena_practice_id, token, debug_file)
    except Exception as e:
        ImportLog.objects.update_or_create(task_name=task_name, defaults={"last_run_at": current_run_time, "status": "failed", "notes": f"Failed during patient sync: {e}"})
        return
    # --- Step 4: Sync Referrals (Concurrent with Rate Limiting) ---
    yield "\nStep 4: Syncing Referrals (using concurrency and rate limiting)..."
    try:
        yield from _sync_referrals(athena_practice_id, token, practice, debug_file)
    except Exception as e:
        logging.error(f"An unexpected error occurred during referral sync: {e}", exc_info=True)
        yield f"ERROR during Referral Sync: {e}. Aborting."
        ImportLog.objects.update_or_create(task_name=task_name, defaults={"last_run_at": current_run_time, "status": "failed", "notes": f"Failed during referral sync: {e}"})
        return
    
    # --- Finalize ---
    final_notes = f"Sync complete. Synced providers, patients, and referrals (created:, updated:)."
    ImportLog.objects.update_or_create(
        task_name=task_name,
        defaults={"last_run_at": current_run_time, "status": "success", "notes": final_notes}
    )
    yield f"\n{final_notes}"

from django.http import HttpResponse
from django.template.loader import render_to_string
import csv
from weasyprint import HTML

@login_required
def generate_quarterly_report(request):
    if request.user.is_superuser:
        base_referrals = Referral.objects.all()
    else:
        try:
            user_practice = request.user.userprofile.practice
            if user_practice:
                base_referrals = Referral.objects.filter(practice=user_practice)
            else:
                base_referrals = Referral.objects.none()
        except (UserProfile.DoesNotExist, AttributeError):
            base_referrals = Referral.objects.none()

    selected_quarters = request.GET.getlist('quarter')
    current_year = timezone.now().year
    
    q_filters = Q()
    if selected_quarters:
        for q in selected_quarters:
            if q == '1': # Q1: Jan 1 - Mar 31
                q_filters |= Q(referral_date__gte=datetime(current_year, 1, 1), referral_date__lte=datetime(current_year, 3, 31))
            elif q == '2': # Q2: Apr 1 - Jun 30
                q_filters |= Q(referral_date__gte=datetime(current_year, 4, 1), referral_date__lte=datetime(current_year, 6, 30))
            elif q == '3': # Q3: Jul 1 - Sep 30
                q_filters |= Q(referral_date__gte=datetime(current_year, 7, 1), referral_date__lte=datetime(current_year, 9, 30))
            elif q == '4': # Q4: Oct 1 - Dec 31
                q_filters |= Q(referral_date__gte=datetime(current_year, 10, 1), referral_date__lte=datetime(current_year, 12, 31))
        
        referrals_in_period = base_referrals.filter(q_filters)
    else:
        referrals_in_period = base_referrals

    referrals_with_provider_in_period = referrals_in_period.filter(provider__isnull=False)
    
    # Main dashboard metrics
    total = referrals_in_period.count()
    in_network = referrals_with_provider_in_period.filter(in_network=True).count()
    out_network = referrals_with_provider_in_period.filter(in_network=False).count()
    total_with_provider = referrals_with_provider_in_period.count()
    in_network_rate = (in_network / total_with_provider * 100.0) if total_with_provider else 0
    out_network_rate = (out_network / total_with_provider * 100.0) if total_with_provider else 0
    
    out_of_network_referrals_with_provider = referrals_in_period.filter(in_network=False, provider__isnull=False)
    total_leakage_cost = out_of_network_referrals_with_provider.aggregate(total_cost=Sum('rvu_cost'))['total_cost'] or Decimal('0.00')
    average_leakage_cost = (total_leakage_cost / out_of_network_referrals_with_provider.count()) if out_of_network_referrals_with_provider.count() > 0 else Decimal('0.00')
    
    completed = referrals_in_period.filter(status__in=[Referral.Status.COMPLETED, Referral.Status.CLOSED]).count()
    completion_rate = (completed / total * 100.0) if total else 0

    dashboard_metrics = {
        'total': total,
        'in_network': in_network,
        'out_network': out_network,
        'in_network_rate': in_network_rate,
        'out_network_rate': out_network_rate,
        'completion_rate': completion_rate,
        'total_leakage_cost': total_leakage_cost,
        'average_leakage_cost': average_leakage_cost,
    }

    # Specialty metrics
    specialties = Provider.objects.values_list('specialty', flat=True).distinct()
    specialty_data = []
    for spec in specialties:
        refs = referrals_in_period.filter(provider__specialty=spec)
        total_spec = refs.count()
        if spec is None:
            in_network_spec = 0
            out_network_spec = 0
        else:
            in_network_spec = refs.filter(in_network=True).count()
            out_network_spec = refs.filter(in_network=False).count()
        in_network_rate_spec = (in_network_spec / total_spec * 100.0) if total_spec else 0
        completion_rate_spec = (refs.filter(status__in=[Referral.Status.COMPLETED, Referral.Status.CLOSED]).count() / total_spec * 100.0) if total_spec else 0
        leakage_cost_spec = refs.filter(in_network=False).aggregate(total_leak=Sum('rvu_cost')).get('total_leak') or 0
        avg_leakage_cost_spec = (leakage_cost_spec / out_network_spec) if out_network_spec else 0

        specialty_data.append({
            'specialty': spec,
            'total': total_spec,
            'in_network': in_network_spec,
            'out_network': out_network_spec,
            'in_network_rate': in_network_rate_spec,
            'completion_rate': completion_rate_spec,
            'leakage_cost': leakage_cost_spec,
            'avg_leakage_cost': avg_leakage_cost_spec,
        })
    
    report_format = request.GET.get('format', 'csv').lower()

    if report_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="quarterly_report.csv"'

        writer = csv.writer(response)
        # Write dashboard metrics
        writer.writerow(['Dashboard Metrics'])
        writer.writerow(['Metric', 'Value'])
        for key, value in dashboard_metrics.items():
            writer.writerow([key.replace('_', ' ').title(), value])
        
        writer.writerow([]) # Blank line
        
        # Write specialty metrics
        writer.writerow(['Specialty Metrics'])
        writer.writerow(['Specialty', 'Total Referrals', 'In-Network', 'Out-of-Network', 'In-Network Rate (%)', 'Completion Rate (%)', 'Total Leakage Cost', 'Average Leakage Cost'])
        for item in specialty_data:
            writer.writerow([
                item['specialty'],
                item['total'],
                item['in_network'],
                item['out_network'],
                f"{item['in_network_rate']:.2f}",
                f"{item['completion_rate']:.2f}",
                f"{item['leakage_cost']:.2f}",
                f"{item['avg_leakage_cost']:.2f}",
            ])
        return response

    elif report_format == 'pdf':
        html_string = render_to_string('analytics/quarterly_report.html', {
            'selected_quarters': selected_quarters,
            'dashboard_metrics': dashboard_metrics,
            'specialty_data': specialty_data,
        })
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quarterly_report.pdf"'
        
        HTML(string=html_string).write_pdf(response)
        
        return response

    else:
        return HttpResponse("Invalid report format specified.", status=400)


