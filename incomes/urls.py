from django.urls import path
from . import views

urlpatterns = [
    path('per_month/', views.incomes_per_month, name='incomes_per_month'),
    path('per_year/', views.incomes_per_year, name='incomes_per_year'),
]
