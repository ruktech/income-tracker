from django.contrib import admin
from .models import Income, Category, UserProfile
from .forms import IncomeForm, CategoryForm

class IncomeAdmin(admin.ModelAdmin):
    form = IncomeForm
    list_display = ('amount', 'date', 'category', 'description', 'recurring', 'user')
    list_filter = ('category', 'recurring', 'user')

class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display = ('name', 'user')
    list_filter = ('user',)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'twilio_to_whatsapp_number')
    list_filter = ('user',)

admin.site.register(Income, IncomeAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(UserProfile, UserProfileAdmin)


