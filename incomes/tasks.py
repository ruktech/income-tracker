import json
import logging
from datetime import timedelta
from typing import Tuple

from django.conf import settings
from django.db.models import Prefetch
from django.db.models.query import QuerySet
from django.utils import timezone
from django.utils.timezone import now
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from .models import Income, UserProfile

logger = logging.getLogger(__name__)


def build_template_variables(income: Income) -> str:
    """Prepare variables for WhatsApp content template."""
    return json.dumps(
        {
            "1": income.user.first_name or income.user.username,
            "2": f"{income.amount:,.2f}",
            "3": income.currency or "USD",
            "4": income.category.name if income.category else "General",
            "5": income.description or "No description",
        }
    )


def get_tomorrows_incomes() -> Tuple["QuerySet[Income]", timezone.datetime.date]:
    """Return active non expired incomes with a reminder due tomorrow."""
    tomorrow = timezone.localdate() + timedelta(days=1)
    return (
        Income.objects.select_related("user", "category")
        .filter(expiration_date__gte=now().date())
        .prefetch_related(Prefetch("user__userprofile", queryset=UserProfile.objects.only("twilio_to_whatsapp_number"))),
        tomorrow,
    )


def send_whatsapp_reminder() -> None:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    incomes, tomorrow = get_tomorrows_incomes()

    for income in incomes:
        occurrences = income.upcoming_occurrences(end_date=tomorrow + timedelta(days=1))
        # print(f"Income #{income.id} occurrences: {occurrences}")

        if tomorrow not in occurrences:
            # print(f"⏭️ Skipping income #{income.id} - not scheduled for {tomorrow}")
            continue

        try:
            user_profile = income.user.userprofile
        except UserProfile.DoesNotExist:
            logger.warning(f"UserProfile missing for user {income.user.id}")
            continue

        to_number = f"whatsapp:{user_profile.whatsapp_number}"
        template_vars = build_template_variables(income)

        try:
            message = client.messages.create(from_=settings.TWILIO_FROM_WHATSAPP_NUMBER, to=to_number, content_sid=settings.TWILIO_WHATSAPP_TEMPLATE_SID, content_variables=template_vars)
            logger.info(f"✅ Reminder sent | Income #{income.id} → {to_number} | SID: {message.sid}")
        except TwilioRestException as e:
            logger.error(f"❌ Twilio failed | Income #{income.id} | {e.code}: {e.msg}")
