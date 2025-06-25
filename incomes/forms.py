import re

from django import forms

from .models import Category, Income, UserProfile

E164_REGEX = r"^\+[1-9]\d{1,14}$"


class UserProfileForm(forms.ModelForm):
    whatsapp_number = forms.CharField(
        required=True,
        label="WhatsApp Number",
        help_text="Enter your WhatsApp number in E.164 format (e.g. +962799306010).",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "+962799306010", "autocomplete": "tel"}),
    )

    class Meta:
        model = UserProfile
        fields = ["whatsapp_number"]  # Do not expose _whatsapp_number_encrypted

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["whatsapp_number"].initial = self.instance.whatsapp_number

    def clean_whatsapp_number(self) -> str:
        number = self.cleaned_data["whatsapp_number"].strip()
        if not re.match(E164_REGEX, number):
            raise forms.ValidationError("Please enter a valid WhatsApp number in E.164 format (e.g. +962799306010).")
        return number

    def save(self, commit: bool = True) -> UserProfile:
        instance = super().save(commit=False)
        instance.whatsapp_number = self.cleaned_data["whatsapp_number"]
        if commit:
            instance.save()
        return instance


class AdminUserProfileForm(forms.ModelForm):
    whatsapp_number = forms.CharField(
        required=True,
        label="WhatsApp Number",
        help_text="Enter your WhatsApp number in E.164 format (e.g. +962799306010).",
    )

    class Meta:
        model = UserProfile
        fields = ["user", "whatsapp_number"]  # Do not expose _whatsapp_number_encrypted

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["whatsapp_number"].initial = self.instance.whatsapp_number

    def clean_whatsapp_number(self) -> str:
        number = self.cleaned_data["whatsapp_number"].strip()
        if not re.match(E164_REGEX, number):
            raise forms.ValidationError("Please enter a valid WhatsApp number in E.164 format (e.g. +962799306010).")
        return number

    def save(self, commit: bool = True) -> UserProfile:
        instance = super().save(commit=False)
        instance.whatsapp_number = self.cleaned_data["whatsapp_number"]
        if commit:
            instance.save()
        return instance


class IncomeForm(forms.ModelForm):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True, help_text="Enter up to 10 digits and 2 decimal places (e.g., 12345678.90)")
    description = forms.CharField(required=True, widget=forms.Textarea)

    class Meta:
        model = Income
        fields = ["amount", "currency", "date", "category", "description", "recurring", "expiration_date"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Amount"}),
            "currency": forms.Select(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Optional notes"}),
            "recurring": forms.Select(attrs={"class": "form-control"}),
            "expiration_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Set category queryset based on user
        if user is not None:
            from .models import Category  # Local import if circular import issues

            self.fields["category"].queryset = Category.objects.filter(user=user, is_deleted=False)
        else:
            self.fields["category"].queryset = Category.objects.none()

        # Set initial values if editing an existing instance
        if self.instance and self.instance.pk:
            self.fields["amount"].initial = self.instance.amount
            self.fields["description"].initial = self.instance.description

    def save(self, commit: bool = True) -> Income:
        instance = super().save(commit=False)
        instance.amount = self.cleaned_data["amount"]
        instance.description = self.cleaned_data["description"]
        if commit:
            instance.save()
        return instance


class AdminIncomeForm(forms.ModelForm):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True, help_text="Enter up to 10 digits and 2 decimal places (e.g., 12345678.90)")
    description = forms.CharField(required=True, widget=forms.Textarea)

    class Meta:
        model = Income
        fields = ["amount", "currency", "date", "category", "description", "recurring", "user", "expiration_date"]

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["amount"].initial = self.instance.amount
            self.fields["description"].initial = self.instance.description

    def save(self, commit: bool = True) -> Income:
        instance = super().save(commit=False)
        instance.amount = self.cleaned_data["amount"]
        instance.description = self.cleaned_data["description"]
        if commit:
            instance.save()
        return instance


class CategoryForm(forms.ModelForm):
    name = forms.CharField(required=True, max_length=255)

    class Meta:
        model = Category
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Category name"})}
        labels = {"name": "Category Name"}

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["name"].initial = self.instance.name

    def save(self, commit: bool = True) -> Category:
        instance = super().save(commit=False)
        instance.name = self.cleaned_data["name"]
        if commit:
            instance.save()
        return instance


class AdminCategoryForm(forms.ModelForm):
    name = forms.CharField(required=True, max_length=255)

    class Meta:
        model = Category
        fields = ["name", "user"]

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["name"].initial = self.instance.name

    def save(self, commit: bool = True) -> Category:
        instance = super().save(commit=False)
        instance.name = self.cleaned_data["name"]
        if commit:
            instance.save()
        return instance
