from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from .models import Income, Category, UserProfile
from django.db.models.signals import pre_delete
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission

User = get_user_model()

class IncomeModelTest(TestCase):
    """This test suite covers:
    - Encryption/decryption for amount, description, and category name
    - Soft delete and restore
    - Expired and not expired incomes
    - Recurring incomes and their occurrences
    - User isolation (multi-user support)
    - Category uniqueness and validation
    - Model validation (`clean`)
    - Unauthorized deletion prevention"""

    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")
        self.category1 = Category.objects.create(user=self.user1)
        self.category1.name = "Salary"
        self.category1.save()
        self.category2 = Category.objects.create(user=self.user2)
        self.category2.name = "Gift"
        self.category2.save()

    def test_income_encryption_and_decryption(self):
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

    def test_income_soft_delete_and_restore(self):
            # Give the user delete permission
        delete_perm = Permission.objects.get(codename="delete_income")
        self.user1.user_permissions.add(delete_perm)

        income = Income.objects.create(
            user=self.user1,
            category=self.category1,
            date=date.today(),
            recurring=Income.RecurringChoices.NO,
            amount=10,
            description="To be deleted"
        )

        income.delete()
        self.assertTrue(income.is_deleted)

        income.restore()
        self.assertFalse(income.is_deleted)

    def test_income_expired_and_not_expired(self):
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

    def test_income_recurring_occurrences(self):
        income = Income.objects.create(
            user=self.user1,
            category=self.category1,
            date=date.today(),
            recurring=Income.RecurringChoices.MONTHLY,
        )
        income.amount = 50
        income.description = "Recurring"
        income.save()
        occurrences = income.upcoming_occurrences(date.today() + timedelta(days=90))
        self.assertGreaterEqual(len(occurrences), 3)

    def test_income_user_isolation(self):
        income1 = Income.objects.create(
            user=self.user1,
            category=self.category1,
            date=date.today(),
            recurring=Income.RecurringChoices.NO,
        )
        income1.amount = 10
        income1.description = "User1"
        income1.save()
        income2 = Income.objects.create(
            user=self.user2,
            category=self.category2,
            date=date.today(),
            recurring=Income.RecurringChoices.NO,
        )
        income2.amount = 20
        income2.description = "User2"
        income2.save()
        self.assertEqual(Income.objects.filter(user=self.user1).count(), 1)
        self.assertEqual(Income.objects.filter(user=self.user2).count(), 1)

    def test_category_encryption_and_uniqueness(self):
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

    def test_income_clean_validation(self):
        income = Income(
            user=self.user1,
            category=self.category1,
            date=date.today(),
            recurring=Income.RecurringChoices.NO,
        )
        income.amount = -10
        income.description = "Short"
        with self.assertRaises(ValueError):
            income.clean()
        income.amount = 10
        income.description = "ThisDescriptionIsWayTooLong"
        with self.assertRaises(ValueError):
            income.clean()


    def test_prevent_unauthorized_deletion(self):
        income = Income.objects.create(
            user=self.user1,
            category=self.category1,
            date=date.today(),
            recurring=Income.RecurringChoices.NO,
            amount=10,
            description="Delete"
        )
        self.user1.user_permissions.clear()
        self.user1.groups.clear()

        with self.assertRaises(PermissionDenied):
            income.delete()