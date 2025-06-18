from __future__ import annotations

import base64
import hashlib
import re
from datetime import date, timedelta
from typing import List, Optional

from cryptography.fernet import Fernet
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import (
    AbstractBaseUser,  # Added for type annotation
    User,
)
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from django.utils import timezone
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _


class OwnerProtectedDeleteMixin:
    """
    A reusable mixin that enforces delete permissions and ownership.
    Use in models with a `user` FK and custom delete/hard_delete logic.
    """

    def _check_permission_and_ownership(self, acting_user: AbstractBaseUser, perm: str) -> None:
        if acting_user is None:
            raise PermissionDenied("Authenticated user is required for deletion.")
        if not acting_user.has_perm(perm):
            raise PermissionDenied(f"You do not have permission: {perm}")
        if self.user != acting_user:
            raise PermissionDenied("You cannot delete an object you don’t own.")


# region Soft and Hard Delete Implementation


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self) -> None:
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self) -> None:
        return super().delete()

    def alive(self) -> None:
        return self.filter(is_deleted=False)

    def dead(self) -> None:
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return self.all_with_deleted().alive()
        # return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_with_deleted(self) -> models.QuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)

    def only_deleted(self) -> models.QuerySet:
        return self.all_with_deleted().dead()


class SoftDeleteModel(OwnerProtectedDeleteMixin, models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteManager()  # For accessing all records, including deleted

    class Meta:
        abstract = True

    def delete(self, using: Optional[str] = None, keep_parents: bool = False, acting_user: AbstractBaseUser | None = None) -> None:
        if acting_user is None:
            raise PermissionDenied("User authentication required.")
        if not acting_user.has_perm("incomes.delete_income"):
            raise PermissionDenied("You do not have delete permission.")
        if self.user != acting_user:
            raise PermissionDenied("You cannot delete income you don’t own.")
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, using: Optional[str] = None, keep_parents: bool = False, acting_user: AbstractBaseUser | None = None) -> None:
        if acting_user is None:
            raise PermissionDenied("User authentication required.")
        if not acting_user.has_perm("incomes.delete_income"):
            raise PermissionDenied("You do not have delete permission.")
        if self.user != acting_user:
            raise PermissionDenied("You cannot delete income you don’t own.")
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self) -> None:
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])

        """Usage example:

            ->Soft delete
            income.delete()

            ->Restore
            income.restore()

            ->Hard delete (permanent)
            income.hard_delete()

            ->Query only non-deleted
            Income.objects.all()

            ->Query all (including deleted)
            Income.all_objects.all_with_deleted()

            ->Query only deleted
            Income.all_objects.only_deleted()

        """


# endregion


class EncryptedModel(models.Model):
    """
    Base model that provides encryption utilities for other models.
    """

    class Meta:
        abstract = True  # This ensures the model is not created in the database

    def _get_encryption_key(self) -> bytes:
        """
        Generate a 32-byte URL-safe encryption key derived from the SECRET_KEY.
        """
        secret_key = settings.SECRET_KEY.encode()  # Convert to bytes
        hashed_key = hashlib.sha256(secret_key).digest()  # Hash the key
        return base64.urlsafe_b64encode(hashed_key[:32])  # Ensure 32 bytes


def default_expiration_date() -> date:
    """Returns a date 3 years from today."""
    return date.today() + timedelta(days=3 * 365)


class UserProfile(EncryptedModel):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    _whatsapp_number_encrypted = models.CharField(
        max_length=255,
        null=False,  # temporarily allow null
        blank=False,
        db_column="twilio_to_whatsapp_number",
        help_text=_("The WhatsApp number to send reminders to for this user."),
    )

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self) -> str:
        return f"{self.user.username}'s Profile"

    def _get_cipher_suite(self) -> Fernet:
        key = self._get_encryption_key()
        return Fernet(key)

    @property
    def whatsapp_number(self) -> str:
        if not self._whatsapp_number_encrypted:
            raise ValueError(_("WhatsApp number is required."))
        try:
            cipher = self._get_cipher_suite()
            return cipher.decrypt(self._whatsapp_number_encrypted.encode()).decode()
        except Exception as e:
            raise ValueError(_("Failed to decrypt WhatsApp number.")) from e

    @whatsapp_number.setter
    def whatsapp_number(self, value: str) -> None:
        if value is None or not isinstance(value, str) or not value.strip():
            raise ValueError(_("WhatsApp number must be a non-empty string."))

        cipher = self._get_cipher_suite()
        self._whatsapp_number_encrypted = cipher.encrypt(value.strip().encode()).decode()


class Category(SoftDeleteModel, EncryptedModel):
    _name_encrypted = models.CharField(max_length=255, db_column="name")
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        help_text=_("The user who owns this category."),
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["_name_encrypted"]
        unique_together = (
            "user",
            "_name_encrypted",
        )  # Enforce uniqueness of name per user

    @property
    def name(self) -> Optional[str]:
        if not self._name_encrypted:
            return None
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        return cipher_suite.decrypt(self._name_encrypted.encode()).decode()

    @name.setter
    def name(self, value: str) -> None:
        if not value or not re.match(r"^[\w\s]+$", value):
            raise ValueError(_("Category name must be alphanumeric and not empty."))
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        self._name_encrypted = cipher_suite.encrypt(value.encode()).decode()

    def clean(self) -> None:
        super().clean()
        # Enforce uniqueness of name per user (case-insensitive)
        if self.name:
            qs = Category.all_objects.filter(user=self.user)
            # Exclude self when updating
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            for cat in qs:
                if cat.name and cat.name.lower() == self.name.lower():
                    raise ValueError(_("Category name must be unique per user."))

    def __str__(self) -> str:
        return self.name


class Income(SoftDeleteModel, EncryptedModel):
    class RecurringChoices(models.TextChoices):
        NO = "NO", _("No Recurrence")
        MONTHLY = "MO", _("Monthly")
        QUARTERLY = "QO", _("Quarterly")
        SEMI_ANNUALLY = "SO", _("Semi-annually")
        ANNUALLY = "YO", _("Annually")

        @classmethod
        def get_interval(cls, value: str) -> Optional[relativedelta]:
            """Return the interval for the recurrence type."""
            intervals = {
                cls.MONTHLY: relativedelta(months=1),
                cls.QUARTERLY: relativedelta(months=3),
                cls.SEMI_ANNUALLY: relativedelta(months=6),
                cls.ANNUALLY: relativedelta(years=1),
            }
            return intervals.get(value)

    class CurrencyChoices(models.TextChoices):
        JOD = "JOD", _("Jordanian Dinar")
        SAR = "SAR", _("Saudi Riyal")
        TRY = "TRY", _("Turkish Lira")
        USD = "USD", _("US Dollar")

    _amount_encrypted = models.CharField(max_length=255, db_column="amount")
    _description_encrypted = models.TextField(blank=False, null=False, default="", db_column="description")
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    recurring = models.CharField(
        max_length=2,
        choices=RecurringChoices.choices,
        default=RecurringChoices.NO,
    )
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices.choices,
        default=CurrencyChoices.USD,
        help_text=_("Currency of the income."),
    )
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, null=False, blank=False)
    expiration_date = models.DateField(
        null=True,
        blank=True,
        default=default_expiration_date,
        help_text=_("The date after which this income is considered expired."),
    )

    @property
    def amount(self) -> Optional[float]:
        if not self._amount_encrypted:
            return None
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        return float(cipher_suite.decrypt(self._amount_encrypted.encode()).decode())

    @amount.setter
    def amount(self, value: float) -> None:
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        self._amount_encrypted = cipher_suite.encrypt(str(value).encode()).decode()

    @property
    def description(self) -> Optional[str]:
        if not self._description_encrypted:
            return None
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        return cipher_suite.decrypt(self._description_encrypted.encode()).decode()

    @description.setter
    def description(self, value: str) -> None:
        if not value:
            raise ValueError("Description is required.")
        value = escape(value)  # Sanitize HTML input
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        self._description_encrypted = cipher_suite.encrypt(value.encode()).decode()

    class Meta:
        verbose_name = _("Income")
        verbose_name_plural = _("Incomes")
        ordering = ["-date"]

    def get_next_occurrence(self, current_date: Optional[date] = None) -> Optional[date]:
        """
        Calculate the next occurrence of the income based on its recurrence type.
        """
        if current_date is None:
            current_date = self.date

        if self.recurring == self.RecurringChoices.NO:
            return None

        interval = self.RecurringChoices.get_interval(self.recurring)
        return current_date + interval if interval else None

    def upcoming_occurrences(self, end_date: date) -> List[date]:
        """
        Generate a list of upcoming occurrences of the income until the given end date.
        """
        occurrences = []
        next_date = self.date

        if self.recurring == self.RecurringChoices.NO:
            if next_date <= end_date:
                occurrences.append(next_date)
            return occurrences

        while next_date <= end_date:
            occurrences.append(next_date)
            next_date = self.get_next_occurrence(next_date)
            if not next_date:
                break

        return occurrences

    def clean(self) -> None:
        super().clean()
        if self.amount is not None and self.amount < 0:
            raise ValueError(_("Amount must be non-negative."))
        if self.description and len(self.description) > 150:
            raise ValidationError(_("Description must not exceed 150 characters."))
