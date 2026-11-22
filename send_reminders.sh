#!/bin/bash
set -e

cd /home/musab/income-tracker
exec /home/musab/.local/bin/uv run --locked python manage.py send_reminders
#cd /home/musab/income-tracker
#/home/musab/.local/bin/uv run manage.py send_reminders
