from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest

from .forms import AdminCategoryForm, AdminIncomeForm, AdminUserProfileForm
from .models import Category, Income, UserProfile


@admin.action(description="Restore selected incomes")
def restore_incomes(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet) -> None:
    for obj in queryset:
        obj.restore()


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    form = AdminIncomeForm
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
        return Income.all_objects.all_with_deleted().select_related("category", "user")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = AdminCategoryForm
    list_display = ("name", "user")
    list_filter = ("user",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = AdminUserProfileForm
    list_display = ("user", "whatsapp_number")
    list_filter = ("user",)
