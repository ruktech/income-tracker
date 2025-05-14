from __future__ import annotations
from datetime import timedelta, date
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Optional, List
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

def default_expiration_date():
    """Returns a date 3 years from today."""
    return date.today() + timedelta(days=3 * 365)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    twilio_to_whatsapp_number = models.CharField(
        max_length=20,
        help_text=_("The WhatsApp number to send reminders to for this user.")
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
class Category(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        help_text=_("The user who owns this category.")
    )

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]
        unique_together = ("user", "name")  # Enforce uniqueness of name per user

    def __str__(self) -> str:
        return self.name


class Income(models.Model):
    class RecurringChoices(models.TextChoices):
        NO = "NO", _("No Recurrence")
        MONTHLY = "MO", _("Monthly")
        QUARTERLY = "QO", _("Quarterly")
        SEMI_ANNUALLY = "SO", _("Semi-annually")

        @classmethod
        def get_interval(cls, value: str) -> Optional[timedelta]:
            """Return the interval for the recurrence type."""
            intervals = {
                cls.MONTHLY: timedelta(days=30),
                cls.QUARTERLY: timedelta(days=90),
                cls.SEMI_ANNUALLY: timedelta(days=180),
            }
            return intervals.get(value)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = models.TextField(blank=True, null=True)
    recurring = models.CharField(
        max_length=2,
        choices=RecurringChoices.choices,
        default=RecurringChoices.NO,
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )
    expiration_date = models.DateField(
        null=True,
        blank=True,
        default=default_expiration_date,
        help_text=_("The date after which this income is considered expired.")
    )

    class Meta:
        verbose_name = _("Income")
        verbose_name_plural = _("Incomes")
        ordering = ["-date"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gte=0),
                name="amount_positive",
            )
        ]


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
        """
        Validate the model's data.
        """
        if self.amount < 0:
            raise ValueError(_("Amount must be non-negative."))