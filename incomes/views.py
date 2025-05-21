from django.contrib.auth import get_user_model, login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
)
from django.shortcuts import redirect
from .models import Income, Category, UserProfile
from .forms import IncomeForm, CategoryForm
from django import forms

User = get_user_model()

# --- User Signup Form ---
class SignupForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ("username", "email")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = False  # Require admin approval
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

    def get_object(self):
        return UserProfile.objects.get(user=self.request.user)

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    fields = ["twilio_to_whatsapp_number"]
    template_name = "userprofile/userprofile_form.html"
    success_url = reverse_lazy("userprofile-detail")

    def get_object(self):
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