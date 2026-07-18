
from decimal import Decimal
from datetime import timedelta
import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .models import DailyBudget, DailyNote, Expense


def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            DailyBudget.objects.create(user=user)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    error = None
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user:
            login(request, user)
            return redirect('home')
        error = 'Your username or password is incorrect.'
    return render(request, 'login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def home(request):
    today = timezone.localdate()
    budget, _ = DailyBudget.objects.get_or_create(user=request.user)
    selected_date = parse_date(request.GET.get('date', '')) or today
    if selected_date > today:
        selected_date = today

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'budget':
            try:
                amount = Decimal(request.POST.get('budget_amount', ''))
                if amount < 0:
                    raise ValueError
                budget.amount = amount
                budget.save()
                messages.success(request, 'Today’s budget was updated.')
            except Exception:
                messages.error(request, 'Please enter a valid budget amount.')
        elif action == 'expense':
            try:
                amount = Decimal(request.POST.get('amount', ''))
                category = request.POST.get('category')
                title = request.POST.get('title', '').strip()
                if amount <= 0 or not title or category not in dict(Expense.Category.choices):
                    raise ValueError
                Expense.objects.create(user=request.user, title=title, amount=amount, category=category, spent_on=selected_date)
                messages.success(request, 'Expense added.')
            except Exception:
                messages.error(request, 'Please complete the expense with a valid amount and category.')
        elif action == 'note':
            content = request.POST.get('content', '').strip()
            if content:
                DailyNote.objects.create(user=request.user, note_date=selected_date, content=content)
                messages.success(request, 'Your note was saved.')
            else:
                messages.error(request, 'Please write a note before saving.')
        return redirect(f"{request.path}?date={selected_date.isoformat()}")

    selected_category = request.GET.get('category', '')
    expenses = Expense.objects.filter(user=request.user, spent_on=selected_date)
    if selected_category in dict(Expense.Category.choices):
        expenses = expenses.filter(category=selected_category)
    spent_today = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    all_today = Expense.objects.filter(user=request.user, spent_on=selected_date)
    chart_rows = all_today.values('category').annotate(total=Sum('amount')).order_by('category')
    colors = ['#6c63ff', '#ff8a65', '#26a69a', '#f4b942', '#ec6c89', '#4b8cff', '#9c6ade']
    chart_data = [
        {'label': Expense.Category(row['category']).label, 'total': float(row['total']), 'color': colors[index % len(colors)]}
        for index, row in enumerate(chart_rows)
    ]
    total_all = all_today.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    day_notes = DailyNote.objects.filter(user=request.user, note_date=selected_date)
    previous_notes = DailyNote.objects.filter(user=request.user).exclude(
        note_date=selected_date
    ).exclude(content='').order_by('-note_date')[:7]
    return render(request, 'home.html', {
        'budget': budget.amount, 'spent_today': total_all, 'remaining': budget.amount - total_all,
        'expenses': expenses, 'categories': Expense.Category.choices, 'selected_category': selected_category,
        'chart_data': chart_data, 'chart_data_json': json.dumps(chart_data), 'today': today,
        'selected_date': selected_date, 'day_notes': day_notes, 'previous_notes': previous_notes,
    })


@login_required(login_url='login')
def analytics(request):
    """Show a seven-day daily spending bar chart for each expense category."""
    today = timezone.localdate()
    start_date = today - timedelta(days=6)
    expenses = Expense.objects.filter(user=request.user, spent_on__range=(start_date, today))
    totals_by_day = {
        (row['category'], row['spent_on'].isoformat()): float(row['total'])
        for row in expenses.values('category', 'spent_on').annotate(total=Sum('amount'))
    }
    dates = [start_date + timedelta(days=offset) for offset in range(7)]
    colors = ['#6c63ff', '#ff8a65', '#26a69a', '#f4b942', '#ec6c89', '#4b8cff', '#9c6ade']
    charts = []
    for index, (value, label) in enumerate(Expense.Category.choices):
        values = [totals_by_day.get((value, day.isoformat()), 0) for day in dates]
        charts.append({
            'label': label, 'color': colors[index], 'values': values,
            'dates': [day.strftime('%d %b') for day in dates], 'total': sum(values),
        })
    return render(request, 'analytics.html', {
        'charts': charts, 'chart_data_json': json.dumps(charts),
        'start_date': start_date, 'today': today,
    })


@login_required(login_url='login')
def statements(request):
    """Display the user's complete expense history with optional filters."""
    expenses = Expense.objects.filter(user=request.user)
    selected_category = request.GET.get('category', '')
    start_date = parse_date(request.GET.get('from', ''))
    end_date = parse_date(request.GET.get('to', ''))
    if selected_category in dict(Expense.Category.choices):
        expenses = expenses.filter(category=selected_category)
    else:
        selected_category = ''
    if start_date:
        expenses = expenses.filter(spent_on__gte=start_date)
    if end_date:
        expenses = expenses.filter(spent_on__lte=end_date)
    total_spent = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    return render(request, 'statements.html', {
        'expenses': expenses, 'total_spent': total_spent,
        'categories': Expense.Category.choices, 'selected_category': selected_category,
        'start_date': start_date, 'end_date': end_date,
    })
