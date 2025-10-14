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


# --- Provider list ---
def provider_list(request):
    query = request.GET.get('q', '').strip()
    providers = Provider.objects.all()
    if query:
        providers = providers.filter(
            Q(full_name__icontains=query)
            | Q(specialty__icontains=query)
            | Q(subspecialty__icontains=query)
            | Q(city__icontains=query)
            | Q(state__icontains=query)
        )
    providers = providers.order_by('full_name')
    return render(request, 'analytics/provider_list.html', {'providers': providers, 'query': query})


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
            patient_id = form.cleaned_data['patient_id']
            patient, _ = Patient.objects.get_or_create(original_id=patient_id)
            provider = form.cleaned_data['provider']
            payer_code = form.cleaned_data.get('payer_code')
            payer = None
            if payer_code:
                payer, _ = Payer.objects.get_or_create(code=payer_code, defaults={'name': payer_code})
            referral = Referral.objects.create(
                patient=patient,
                provider=provider,
                payer=payer,
                specialty=form.cleaned_data.get('specialty') or provider.specialty,
                status=form.cleaned_data['status'],
                in_network=form.cleaned_data['in_network'],
                cost_value=form.cleaned_data['cost_value'],
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


# --- Delete referral ---
def delete_referral(request, pk):
    """
    Delete a referral by its primary key.  Redirect back to the dashboard.
    """
    referral = get_object_or_404(Referral, pk=pk)
    referral.delete()
    return redirect('analytics_dashboard')
