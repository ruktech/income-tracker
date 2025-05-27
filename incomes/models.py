from __future__ import annotations
from datetime import timedelta, date
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing import Optional, List
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete
from django.utils.html import escape
from django.dispatch import receiver
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import hashlib
from django.core.exceptions import PermissionDenied
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
import re

class OwnerProtectedDeleteMixin:
    """
    A reusable mixin that enforces delete permissions and ownership.
    Use in models with a `user` FK and custom delete/hard_delete logic.
    """

    def _check_permission_and_ownership(self, acting_user, perm: str):
        if acting_user is None:
            raise PermissionDenied("Authenticated user is required for deletion.")
        if not acting_user.has_perm(perm):
            raise PermissionDenied(f"You do not have permission: {perm}")
        if self.user != acting_user:
            raise PermissionDenied("You cannot delete an object you don’t own.")
        

#region Soft and Hard Delete Implementation

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return self.all_with_deleted().alive()
        # return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def only_deleted(self):
        return self.all_with_deleted().dead()


class SoftDeleteModel(OwnerProtectedDeleteMixin, models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteManager()  # For accessing all records, including deleted

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, acting_user=None):
        if acting_user is None:
            raise PermissionDenied("User authentication required.")
        if not acting_user.has_perm("incomes.delete_income"):
            raise PermissionDenied("You do not have delete permission.")
        if self.user != acting_user:
            raise PermissionDenied("You cannot delete income you don’t own.")
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self, using=None, keep_parents=False, acting_user=None):
        if acting_user is None:
            raise PermissionDenied("User authentication required.")
        if not acting_user.has_perm("incomes.delete_income"):
            raise PermissionDenied("You do not have delete permission.")
        if self.user != acting_user:
            raise PermissionDenied("You cannot delete income you don’t own.")
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    
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

#endregion

class EncryptedModel(models.Model):
    """
    Base model that provides encryption utilities for other models.
    """
    class Meta:
        abstract = True  # This ensures the model is not created in the database

    def _get_encryption_key(self):
        """
        Generate a 32-byte URL-safe encryption key derived from the SECRET_KEY.
        """
        secret_key = settings.SECRET_KEY.encode()  # Convert to bytes
        hashed_key = hashlib.sha256(secret_key).digest()  # Hash the key
        return base64.urlsafe_b64encode(hashed_key[:32])  # Ensure 32 bytes
        
def default_expiration_date():
    """Returns a date 3 years from today."""
    return date.today() + timedelta(days=3 * 365)

class UserProfile(EncryptedModel):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    twilio_to_whatsapp_number = models.CharField(
        max_length=20,
        help_text=_("The WhatsApp number to send reminders to for this user.")
    )

    def save(self, *args, **kwargs):
        # Encrypt the WhatsApp number
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        self.twilio_to_whatsapp_number = cipher_suite.encrypt(
            self.twilio_to_whatsapp_number.encode()
        ).decode()

        super().save(*args, **kwargs)

    def get_decrypted_whatsapp_number(self):
        # Decrypt the WhatsApp number
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        return cipher_suite.decrypt(self.twilio_to_whatsapp_number.encode()).decode()

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
class Category(SoftDeleteModel, EncryptedModel):
    _name_encrypted = models.CharField(max_length=255, db_column='name')
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        help_text=_("The user who owns this category.")
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["_name_encrypted"]
        unique_together = ("user", "_name_encrypted")  # Enforce uniqueness of name per user

    @property
    def name(self):
        if not self._name_encrypted:
            return None
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        return cipher_suite.decrypt(self._name_encrypted.encode()).decode()

    @name.setter
    def name(self, value):
        if not value or not re.match(r'^[\w\s]+$', value):
            raise ValueError(_("Category name must be alphanumeric and not empty."))
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        self._name_encrypted = cipher_suite.encrypt(value.encode()).decode()

    def clean(self):
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

    def __str__(self):
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

    _amount_encrypted = models.CharField(max_length=255, db_column='amount')
    _description_encrypted = models.TextField(blank=False, null=False,  default="", db_column='description')
    # amount = models.CharField(max_length=255)
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    # description = models.TextField(blank=True, null=True)
    recurring = models.CharField(
        max_length=2,
        choices=RecurringChoices.choices,
        default=RecurringChoices.NO,
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        null=False,
        blank=False
    )
    expiration_date = models.DateField(
        null=True,
        blank=True,
        default=default_expiration_date,
        help_text=_("The date after which this income is considered expired.")
    )

    @property
    def amount(self):
        if not self._amount_encrypted:
            return None
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        return float(cipher_suite.decrypt(self._amount_encrypted.encode()).decode())

    @amount.setter
    def amount(self, value):
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        self._amount_encrypted = cipher_suite.encrypt(str(value).encode()).decode()

    @property
    def description(self):
        if not self._description_encrypted:
            return None
        encryption_key = self._get_encryption_key()
        cipher_suite = Fernet(encryption_key)
        return cipher_suite.decrypt(self._description_encrypted.encode()).decode()

    @description.setter
    def description(self, value):
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

    def clean(self):
        super().clean()
        if self.amount is not None and self.amount < 0:
            raise ValueError(_("Amount must be non-negative."))
        if self.description and len(self.description) > 150:
            raise ValidationError(_("Description must not exceed 150 characters."))
    
    #objects = IncomeQuerySet.as_manager()
