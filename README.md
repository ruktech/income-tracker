# Income Tracker

**Income Tracker** is a Django app that tracks and manages all incoming payments, with automatic WhatsApp notifications via Twilio. It’s ideal for personal, small business, or SaaS needs—reminding you or your customers of any upcoming income (rent, bonds, salary, service renewals, and more). All sensitive data is encrypted at rest and only accessible to the project owner.

---

## Features

- **WhatsApp Reminders**: Automatic WhatsApp notifications (via Twilio) before an income is due.
- **Recurring Incomes**: Handles recurring payments (monthly, quarterly, semi-annual, annual).
- **Categories**: Group and filter incomes (bonds, rent, salary, customer payments, etc).
- **Customer Notifications**: Remind customers (e.g. for service or hosting renewals).
- **Monthly Reports**: Visualize all accrued and upcoming incomes per month/category.
- **Field Encryption**: All key fields are encrypted with a key derived from `SECRET_KEY`—only visible to the project owner.
- **Role-Specific Forms**: Admin/staff and user forms for clean management.
- **Safe Environment**: Uses [uv](https://github.com/astral-sh/uv) for Python env and [ruff](https://github.com/astral-sh/ruff) for linting/formatting.
- **Cron-Friendly**: Management command to send reminders, easy to schedule.
- **Postgres-ready**: Out-of-the-box production database config.

---

## Quickstart

### 1. Clone & Initialize

```bash
git clone https://github.com/YOURUSERNAME/income-tracker.git
cd income-tracker
uv init income-tracker .
```

### 2. Add Dependencies

```bash
uv add django twilio python-dotenv cryptography python-dateutil ruff
```
*Add any extras as needed.*

### 3. Set Up Environment

- Copy the example and fill your real values:
    ```bash
    cp .env.example .env
    ```

#### `.env.example`
```env
DEBUG=True
SECRET_KEY='change-this-very-secret-key'
ALLOWED_HOSTS=localhost,127.0.0.1

# Twilio
TWILIO_ACCOUNT_SID='your_account_sid'
TWILIO_AUTH_TOKEN='your_auth_token'
TWILIO_WHATSAPP_TEMPLATE_SID='your_template_sid'
TWILIO_FROM_WHATSAPP_NUMBER='whatsapp:+123456789'

# PostgreSQL (production only)
POSTGRES_DB=incomedb
POSTGRES_USER=incomeuser
POSTGRES_PASSWORD='superstrongdbpassword'
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

---

### 4. Database & User Setup

```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser
```

---

### 5. Run the Server

```bash
uv run python manage.py runserver
```

#### (Optional) Create a Fast Alias

Add this to your shell config (`.bashrc`, `.zshrc`, etc):

```sh
alias uvm='uv run python manage.py'
```

Now you can run, for example:

```bash
uvm runserver
uvm makemigrations
uvm send_reminders
```

---

### 6. Lint & Format

```bash
uv run ruff check .
uv run ruff format .
```

---

## Scheduled Reminders (CRON)

Set up a daily cron job to trigger WhatsApp reminders for incomes due tomorrow.

Edit your crontab with `crontab -e` and add:

```cron
0 7 * * * cd /path/to/income-tracker && uv run python manage.py send_reminders
```
This example sends reminders every day at 7:00 AM. Adjust the path and time as needed.

---

## Usage

- **Add/Manage Incomes:** Through the web UI (CRUD views for incomes, categories, and user profiles).
- **Reports:** Go to `/incomes/reports/` for a monthly summary.
- **WhatsApp Reminders:** Automatic for upcoming incomes, or run manually with:
    ```bash
    uv run python manage.py send_reminders
    ```
- **Categories:** Assign incomes to custom categories for granular reporting.
- **Encryption:** Data is decrypted only within the Django project context (shell or admin).

---

## Directory Structure

```
income-tracker/
├── incomes/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── management/commands/send_reminders.py
│   └── ...
├── IncomeTracker/           # Django project root
├── requirements.txt         # (auto-managed by uv)
├── .env.example
├── .env
├── manage.py
└── ...
```

---

## Security & Best Practices

- Keep your `.env` file **secret**—never commit real secrets!
- Use a strong `SECRET_KEY` for encryption and Django security.
- Use Postgres and `DEBUG=False` for production.
- All user income/category data is isolated; only superuser can view all.

---

## License

MIT

---

## Contributing

PRs and issues welcome!  
- Run `uv run ruff check .` before pushing.
- Follow code style and simple, readable patterns.

---
