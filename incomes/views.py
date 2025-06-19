import calendar
from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Tuple

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView
from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from .forms import CategoryForm, IncomeForm, UserProfileForm
from .models import Category, Income, UserProfile

User = get_user_model()


# --- User Signup Form ---
class SignupForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ("username", "email")

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("password1")
        pw2 = cleaned_data.get("password2")

        if pw1 != pw2:
            raise forms.ValidationError("Passwords do not match.")

        try:
            validate_password(pw1, user=None)
        except ValidationError as e:
            self.add_error("password1", e)

        return cleaned_data

    def save(self, commit: bool = True) -> AbstractBaseUser:
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False
        if commit:
            user.save()
        return user


# --- Signup View ---
class SignupView(FormView):
    template_name = "registration/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Account created. Await admin approval.")
        return super().form_valid(form)


# --- User Data Isolation Mixin ---
class UserIsOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return obj.user == self.request.user


# --- Income Views ---
class IncomeListView(LoginRequiredMixin, ListView):
    model = Income
    template_name = "incomes/income_list.html"
    context_object_name = "incomes"

    def get_queryset(self):
        return Income.objects.filter(user=self.request.user, is_deleted=False)


class IncomeDetailView(UserIsOwnerMixin, DetailView):
    model = Income
    template_name = "incomes/income_detail.html"


class IncomeCreateView(LoginRequiredMixin, CreateView):
    model = Income
    form_class = IncomeForm
    template_name = "incomes/income_form.html"
    success_url = reverse_lazy("income-list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class IncomeUpdateView(UserIsOwnerMixin, UpdateView):
    model = Income
    form_class = IncomeForm
    template_name = "incomes/income_form.html"
    success_url = reverse_lazy("income-list")


class IncomeDeleteView(UserIsOwnerMixin, DeleteView):
    model = Income
    template_name = "incomes/income_confirm_delete.html"
    success_url = reverse_lazy("income-list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete(acting_user=request.user)  # Soft delete with permission check
        return redirect(self.success_url)


# --- Category Views ---
class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = "categories/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user, is_deleted=False)


class CategoryDetailView(UserIsOwnerMixin, DetailView):
    model = Category
    template_name = "categories/category_detail.html"


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "categories/category_form.html"
    success_url = reverse_lazy("category-list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoryUpdateView(UserIsOwnerMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "categories/category_form.html"
    success_url = reverse_lazy("category-list")


class CategoryDeleteView(UserIsOwnerMixin, DeleteView):
    model = Category
    template_name = "categories/category_confirm_delete.html"
    success_url = reverse_lazy("category-list")

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete(acting_user=request.user)  # Soft delete with permission check
        return redirect(self.success_url)


# --- UserProfile Views ---
class UserProfileDetailView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = "userprofile/userprofile_detail.html"

    def get_object(self) -> UserProfile:
        return UserProfile.objects.get(user=self.request.user)


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = "userprofile/userprofile_form.html"
    success_url = reverse_lazy("userprofile-detail")

    def get_object(self) -> UserProfile:
        return UserProfile.objects.get(user=self.request.user)


# --- Authentication Views (Django built-in) ---
class CustomLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        if not form.get_user().is_active:
            messages.error(self.request, "Account inactive. Await admin approval.")
            return redirect("login")
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("logged_out")
    http_method_names = ["get", "post", "head", "options"]

    def dispatch(self, request, *args, **kwargs):
        # Always log out the user, regardless of method
        if request.user.is_authenticated:
            logout(request)
        return super().dispatch(request, *args, **kwargs)


# Password reset views use Django's built-in templates and logic
CustomPasswordResetView = PasswordResetView
CustomPasswordResetDoneView = PasswordResetDoneView
CustomPasswordResetConfirmView = PasswordResetConfirmView
CustomPasswordResetCompleteView = PasswordResetCompleteView


# --- Report Views ---
class ReportView(LoginRequiredMixin, TemplateView):
    template_name = "incomes/report.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context: Dict[str, Any] = super().get_context_data(**kwargs)
        user = self.request.user
        today: date = timezone.localdate()

        selected_year, selected_month = self._get_selected_month_year(today)
        category_id = self.request.GET.get("category")

        incomes_qs = self._get_filtered_incomes(user.id, selected_year, selected_month, category_id)
        month_end = self._get_month_end(selected_year, selected_month)

        accrued, upcoming = self._get_occurrences(incomes_qs, selected_year, selected_month, today, month_end)
        all_incomes = accrued + upcoming

        context.update(
            {
                "selected_year": selected_year,
                "selected_month": selected_month,
                "years": list(range(today.year, today.year - 10, -1)),
                "months": [(i, calendar.month_name[i]) for i in range(1, 13)],
                "categories": Category.objects.filter(user=user, is_deleted=False),
                "selected_category": int(category_id) if category_id and category_id.isdigit() else None,
                "accrued_total": sum(item["income"].amount for item in accrued),
                "upcoming_total": sum(item["income"].amount for item in upcoming),
                "all_total": sum(item["income"].amount for item in all_incomes),
                "accrued_incomes": accrued,
                "upcoming_incomes": upcoming,
                "all_incomes": all_incomes,
                "currency_totals": self._get_currency_totals(all_incomes),
            }
        )

        return context

    def _get_selected_month_year(self, today: date) -> Tuple[int, int]:
        year = self.request.GET.get("year")
        month = self.request.GET.get("month")
        selected_year = int(year) if year and year.isdigit() else today.year
        selected_month = int(month) if month and month.isdigit() else today.month
        return selected_year, selected_month

    def _get_month_end(self, year: int, month: int) -> date:
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, last_day)

    def _get_filtered_incomes(self, user_id: int, year: int, month: int, category_id: str | None) -> models.QuerySet:
        month_start = date(year, month, 1)
        incomes_qs = Income.objects.filter(user_id=user_id, is_deleted=False)

        if category_id and category_id.isdigit():
            incomes_qs = incomes_qs.filter(category_id=int(category_id))

        incomes_qs = incomes_qs.filter(models.Q(expiration_date__isnull=True) | models.Q(expiration_date__gte=month_start))
        return incomes_qs

    def _get_occurrences(self, incomes_qs: models.QuerySet, year: int, month: int, today: date, month_end: date) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        occurrences: List[Tuple[date, Income]] = []

        for income in incomes_qs:
            last_date = min([d for d in [income.expiration_date, month_end] if d])
            for occ_date in income.upcoming_occurrences(last_date):
                if occ_date.year == year and occ_date.month == month and (income.expiration_date is None or occ_date <= income.expiration_date):
                    occurrences.append((occ_date, income))

        occurrences.sort(key=lambda x: x[0])

        accrued = [dict(date=odate, income=inc) for odate, inc in occurrences if odate <= today]
        upcoming = [dict(date=odate, income=inc) for odate, inc in occurrences if odate > today]

        return accrued, upcoming

    def _get_currency_totals(self, incomes: List[Dict[str, Any]]) -> List[Tuple[str, float]]:
        currency_totals: defaultdict[str, float] = defaultdict(float)
        for item in incomes:
            currency = getattr(item["income"], "currency", "JOD")
            currency_totals[currency] += float(item["income"].amount)
        return sorted(currency_totals.items())
