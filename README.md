# Copilot Instructions for Project Refactor

# We're modifying an existing Django project that tracks income and sends WhatsApp reminders.
# The main files include: tasks.py, send_reminders.py, and relevant models/views/admin.

# Step-by-step goals:

# 1. MULTI-USER SUPPORT:
#    - Add user-specific data handling.
#    - Each user should see and manage only their own incomes.
#    - Migrate existing income records to a new user "sameer".

# 2. EXPIRATION:
#    - Add an expiration date field to income records.
#    - Expired incomes should not trigger reminders.

# 3. SECURITY:
#    - Treat income data as sensitive.
#    - Consider hashing or encrypting all income-related fields (amount, category, description).

# 4. REPORTS:
#    - Add reporting functionality:
#      - Income per year
#      - Income per category
#      - Income per month

# 5. SOFT DELETE:
#    - Replace hard deletion with soft delete (e.g., is_active or deleted_at pattern).
#    - Ensure soft-deleted records don't show in default queries or reports.

# 6. PRODUCTION-READY:
#    - Refactor project for production use.
#    - Apply best practices:
#      - Environment-based settings
#      - Secure WhatsApp integration
#      - Logging, error handling
#      - Testing with pytest
#      - Docker support (optional)

# Important: Keep code clean, readable, and follow Django CBV patterns where applicable.
# Focus on simplicity and privacy — especially due to financial data.

# Let's begin with step 1: add multi-user support to the Income model.
