from django import forms
from .models import Income, Category

class IncomeForm(forms.ModelForm):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        help_text="Enter up to 10 digits and 2 decimal places (e.g., 12345678.90)"
    )
    description = forms.CharField(required=True, widget=forms.Textarea)

    class Meta:
        model = Income
        fields = ['amount', 'date', 'category', 'description', 'recurring', 'user', 'expiration_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['amount'].initial = self.instance.amount
            self.fields['description'].initial = self.instance.description

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.amount = self.cleaned_data['amount']
        instance.description = self.cleaned_data['description']
        if commit:
            instance.save()
        return instance
    
class CategoryForm(forms.ModelForm):
    name = forms.CharField(required=True, max_length=255)

    class Meta:
        model = Category
        fields = ['name', 'user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['name'].initial = self.instance.name

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.name = self.cleaned_data['name']
        if commit:
            instance.save()
        return instance