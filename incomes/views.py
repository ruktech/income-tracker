from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from .models import Income, Category
from django.db.models.functions import TruncMonth, TruncYear
from django.db.models import Sum
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth.decorators import login_required


@login_required
def incomes_per_month(request):
    incomes = Income.objects.filter(user=request.user, expiration_date__gte=now().date())
    categories = Category.objects.filter(user=request.user)
    end_date = now().date() + timedelta(days=365)  # Adjust this as needed
    income_data = []

    for income in incomes:
        if income.recurring == 'NO':
            income_data.append({'date': income.date, 'amount': income.amount, 'category': income.category.name})
        else:
            occurrences = income.upcoming_occurrences(end_date)
            for occurrence in occurrences:
                income_data.append({'date': occurrence, 'amount': income.amount, 'category': income.category.name})

    # Aggregate data by month and category
    income_data = sorted(income_data, key=lambda x: x['date'])
    monthly_data = {}
    for income in income_data:
        month = income['date'].strftime('%Y-%m')
        category = income['category']
        if month not in monthly_data:
            monthly_data[month] = {category.name: 0 for category in categories}
        if category not in monthly_data[month]:
            monthly_data[month][category] = 0
        monthly_data[month][category] += income['amount']

    return render(request, 'incomes_per_month.html', {'incomes': monthly_data, 'categories': categories})

@login_required
def incomes_per_year(request):
    incomes = Income.objects.filter(user=request.user, expiration_date__gte=now().date())
    categories = Category.objects.filter(user=request.user)
    end_date = now().date() + timedelta(days=365)  # Adjust this as needed
    income_data = []

    for income in incomes:
        if income.recurring == 'NO':
            income_data.append({'date': income.date, 'amount': income.amount, 'category': income.category.name})
        else:
            occurrences = income.upcoming_occurrences(end_date)
            for occurrence in occurrences:
                income_data.append({'date': occurrence, 'amount': income.amount, 'category': income.category.name})

    # Aggregate data by year and category
    income_data = sorted(income_data, key=lambda x: x['date'])
    yearly_data = {}
    for income in income_data:
        year = income['date'].strftime('%Y')
        category = income['category']
        if year not in yearly_data:
            yearly_data[year] = {category.name: 0 for category in categories}
        if category not in yearly_data[year]:
            yearly_data[year][category] = 0
        yearly_data[year][category] += income['amount']

    return render(request, 'incomes_per_year.html', {'incomes': yearly_data, 'categories': categories})
