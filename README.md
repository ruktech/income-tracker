# Copilot Instructions for Project Refactor

# We're modifying an existing Django project that tracks income and sends WhatsApp reminders.
# The main files include: tasks.py, send_reminders.py, and relevant models/views/admin.

# Step-by-step goals:

# 1. MULTI-USER SUPPORT:
#    - Add user-specific data handling.
#    - Each user should see and manage only their own incomes.

# 2. REPORTS:
#    - Add reporting functionality:
#      - Income per year
#      - Income per category
#      - Income per month
# 3. Database:
#    - use postgres on prodection make db url based on debug values.


# Important: Keep code clean, readable, and follow Django CBV patterns where applicable.
# Focus on simplicity and privacy — especially due to financial data. make productions raedy and robust.

# Let's begin with step 1: add multi-user support to the Income model.
