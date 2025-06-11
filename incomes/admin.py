from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest

from .forms import CategoryForm, IncomeForm
from .models import Category, Income, UserProfile


@admin.action(description="Restore selected incomes")
def restore_incomes(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet) -> None:
    for obj in queryset:
        obj.restore()


class IncomeAdmin(admin.ModelAdmin):
    form = IncomeForm
    list_display = (
        "amount",
        "currency",
        "date",
        "category",
        "description",
        "recurring",
        "user",
        "is_deleted",
    )
    list_filter = ("category", "recurring", "user", "is_deleted")
    actions = [restore_incomes]
    date_hierarchy = "date"
    readonly_fields = ("is_deleted",)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        # Show all records, including soft-deleted
        return Income.all_objects.all_with_deleted()


class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display = ("name", "user")
    list_filter = ("user",)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "twilio_to_whatsapp_number")
    list_filter = ("user",)


admin.site.register(Income, IncomeAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
