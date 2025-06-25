from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from .forms import CategoryForm, IncomeForm, UserProfileForm
from .models import Category, Income, UserProfile

User = get_user_model()


class BaseSetupMixin:
    """Reusable setup for user, categories, and login helpers."""

    user1: AbstractBaseUser
    user2: AbstractBaseUser
    category1: Category
    category2: Category

    def setUp(self) -> None:
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")
        self.category1 = Category.objects.create(user=self.user1)
        self.category1.name = "Salary"
        self.category1.save()
        self.category2 = Category.objects.create(user=self.user2)
        self.category2.name = "Gift"
        self.category2.save()

    def login(self, username: str = "user1", password: str = "pass") -> None:
        self.client = Client()
        self.client.login(username=username, password=password)


class IncomeModelTest(BaseSetupMixin, TestCase):
    """Test Income and Category model logic including encryption, soft delete, validation, user isolation, and recurring incomes."""

    def test_income_encryption_and_decryption(self) -> None:
        income = Income.objects.create(
            user=self.user1,
            category=self.category1,
            date=date.today(),
            recurring=Income.RecurringChoices.NO,
            expiration_date=date.today() + timedelta(days=10),
        )
        income.amount = 1234.56
        income.description = "TestDesc"
        income.save()
        income.refresh_from_db()
        self.assertEqual(income.amount, 1234.56)
        self.assertEqual(income.description, "TestDesc")

    def test_income_soft_delete_and_restore(self) -> None:
        delete_perm = Permission.objects.get(codename="delete_income")
        self.user1.user_permissions.add(delete_perm)
        income = Income.objects.create(user=self.user1, category=self.category1, date=date.today(), recurring=Income.RecurringChoices.NO, amount=10, description="To be deleted")
        income.delete(acting_user=self.user1)
        self.assertTrue(income.is_deleted)
        income.restore()
        self.assertFalse(income.is_deleted)

    def test_income_expired_and_not_expired(self) -> None:
        expired_income = Income.objects.create(
            user=self.user1,
            category=self.category1,
            date=date.today() - timedelta(days=365),
            recurring=Income.RecurringChoices.NO,
            expiration_date=date.today() - timedelta(days=1),
        )
        expired_income.amount = 10
        expired_income.description = "Expired"
        expired_income.save()
        not_expired_income = Income.objects.create(
            user=self.user1,
            category=self.category1,
            date=date.today(),
            recurring=Income.RecurringChoices.NO,
            expiration_date=date.today() + timedelta(days=10),
        )
        not_expired_income.amount = 20
        not_expired_income.description = "NotExpired"
        not_expired_income.save()
        self.assertTrue(expired_income.expiration_date < date.today())
        self.assertTrue(not_expired_income.expiration_date > date.today())

    def test_income_recurring_occurrences(self) -> None:
        income = Income.objects.create(user=self.user1, category=self.category1, date=date.today(), recurring=Income.RecurringChoices.MONTHLY)
        income.amount = 50
        income.description = "Recurring"
        income.save()
        occurrences = income.upcoming_occurrences(date.today() + timedelta(days=90))
        self.assertGreaterEqual(len(occurrences), 3)

    def test_income_user_isolation(self) -> None:
        income1 = Income.objects.create(user=self.user1, category=self.category1, date=date.today(), recurring=Income.RecurringChoices.NO, amount=10, description="User1")
        income2 = Income.objects.create(user=self.user2, category=self.category2, date=date.today(), recurring=Income.RecurringChoices.NO, amount=20, description="User2")
        self.assertEqual(Income.objects.filter(user=self.user1).count(), 1)
        self.assertEqual(Income.objects.filter(user=self.user2).count(), 1)
        self.assertNotEqual(income1.user, income2.user)

    def test_category_encryption_and_uniqueness(self) -> None:
        with self.assertRaises(ValueError):
            cat = Category(user=self.user1)
            cat.name = "Not@Alpha"
            cat.full_clean()
            cat.save()
        # Unique per user
        cat2 = Category(user=self.user1)
        cat2.name = "Salary"
        with self.assertRaises(ValueError):
            cat2.full_clean()
            cat2.save()

    def test_income_clean_validation(self) -> None:
        income = Income(user=self.user1, category=self.category1, date=date.today(), recurring=Income.RecurringChoices.NO)
        income.amount = -10
        income.description = "Short"
        with self.assertRaises(ValueError):
            income.clean()
        income.amount = 10
        income.description = "X" * 200  # Too long
        with self.assertRaises(ValidationError):
            income.clean()

    def test_prevent_unauthorized_deletion(self) -> None:
        income = Income.objects.create(user=self.user1, category=self.category1, date=date.today(), recurring=Income.RecurringChoices.NO, amount=10, description="Delete")
        self.user1.user_permissions.clear()
        self.user1.groups.clear()
        with self.assertRaises(PermissionDenied):
            income.delete(acting_user=self.user1)

    def test_category_str_returns_decrypted(self) -> None:
        self.assertEqual(str(self.category1), "Salary")
        self.assertEqual(str(self.category2), "Gift")


class FormTest(BaseSetupMixin, TestCase):
    """Test custom forms for validation and field constraints."""

    def test_income_form_valid(self) -> None:
        form = IncomeForm(
            data={
                "amount": 100,
                "currency": "USD",
                "date": date.today(),
                "category": self.category1.pk,
                "description": "Salary income",
                "recurring": Income.RecurringChoices.NO,
                "expiration_date": date.today() + timedelta(days=100),
            },
            user=self.user1,
        )
        self.assertTrue(form.is_valid())
        income = form.save(commit=False)
        self.assertEqual(income.amount, 100)

    def test_income_form_invalid_description(self) -> None:
        form = IncomeForm(
            data={
                "amount": 100,
                "currency": "USD",
                "date": date.today(),
                "category": self.category1.pk,
                "description": "",
                "recurring": Income.RecurringChoices.NO,
                "expiration_date": date.today() + timedelta(days=100),
            },
            user=self.user1,
        )
        self.assertFalse(form.is_valid())

    def test_category_form_validation(self) -> None:
        form = CategoryForm(data={"name": "TestCat"})
        self.assertTrue(form.is_valid())
        cat = form.save(commit=False)
        self.assertEqual(cat.name, "TestCat")
        bad_form = CategoryForm(data={"name": ""})
        self.assertFalse(bad_form.is_valid())

    def test_user_profile_form(self) -> None:
        userprofile = UserProfile.objects.create(user=self.user1)
        userprofile.whatsapp_number = "+962799306010"
        userprofile.save()
        form = UserProfileForm(data={"whatsapp_number": "+962799306010"}, instance=userprofile)
        self.assertTrue(form.is_valid())
        profile = form.save(commit=False)
        self.assertTrue(profile.whatsapp_number.startswith("+962"))


class ViewTest(BaseSetupMixin, TestCase):
    """Test major views for permissions, redirects, context, and expected data."""

    def setUp(self) -> None:
        super().setUp()
        self.client = Client()
        self.client.login(username="user1", password="pass")

    def test_income_list_view(self) -> None:
        url = reverse("income-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("incomes", resp.context)

    def test_category_list_view(self) -> None:
        url = reverse("category-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("categories", resp.context)

    def test_income_create_view(self) -> None:
        url = reverse("income-create")
        data = {
            "amount": 500,
            "currency": "USD",
            "date": date.today(),
            "category": self.category1.pk,
            "description": "Bonus",
            "recurring": Income.RecurringChoices.NO,
            "expiration_date": date.today() + timedelta(days=10),
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)  # Redirect to list on success

    def test_report_view_filters_and_soft_deleted(self) -> None:
        today = date.today()
        prev_year = today.year - 1
        income1 = Income.objects.create(user=self.user1, category=self.category1, date=today.replace(year=prev_year), recurring=Income.RecurringChoices.NO, amount=100, description="PrevYearAccrued")
        income2 = Income.objects.create(user=self.user1, category=self.category1, date=today, recurring=Income.RecurringChoices.NO, amount=200, description="CurrentYearAccrued")
        delete_perm = Permission.objects.get(codename="delete_income")
        self.user1.user_permissions.add(delete_perm)
        income1.delete(acting_user=self.user1)
        resp = self.client.get(reverse("income-report"), {"year": prev_year, "month": income1.date.month})
        self.assertNotContains(resp, str(int(income1.amount)))
        resp = self.client.get(reverse("income-report"), {"year": today.year})
        self.assertNotContains(resp, str(income1.amount))
        resp = self.client.get(reverse("income-report"))
        self.assertContains(resp, str(income2.amount))

    def test_login_required_redirect(self) -> None:
        client = Client()
        url = reverse("income-list")
        resp = client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp.url)


class AdminTest(BaseSetupMixin, TestCase):
    """Basic admin checks for list views and permissions."""

    def setUp(self) -> None:
        super().setUp()
        self.admin_user = User.objects.create_superuser(username="admin", password="adminpass", email="admin@ex.com")
        self.client = Client()
        self.client.login(username="admin", password="adminpass")

    def test_income_admin_list(self) -> None:
        url = reverse("admin:incomes_income_changelist")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_category_admin_list(self) -> None:
        url = reverse("admin:incomes_category_changelist")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
