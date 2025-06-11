from django.core.management.base import BaseCommand

from incomes.tasks import send_whatsapp_reminder


class Command(BaseCommand):
    help = "Send WhatsApp reminders for incomes"

    def handle(self, *args, **kwargs) -> None:
        send_whatsapp_reminder()
