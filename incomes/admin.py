from django.contrib import admin
from .models import Income, Category, UserProfile
from .forms import IncomeForm, CategoryForm

def restore_incomes(modeladmin, request, queryset):
    for obj in queryset:
        obj.restore()
restore_incomes.short_description = "Restore selected incomes"

class IncomeAdmin(admin.ModelAdmin):
    form = IncomeForm
    list_display = ('amount', 'date', 'category', 'description', 'recurring', 'user', 'is_deleted')
    list_filter = ('category', 'recurring', 'user', 'is_deleted')
    actions = [restore_incomes]

    def get_queryset(self, request):
        # Show all records, including soft-deleted
        return Income.all_objects.all_with_deleted()

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


