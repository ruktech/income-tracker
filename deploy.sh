#!/bin/bash

set -e  # Exit on any error

echo "🔄 Restarting IncomeTracker (Gunicorn)..."
sudo systemctl restart incometracker

echo "🔄 Reloading Nginx..."
sudo nginx -t
sudo systemctl reload nginx

echo "✅ Deployment complete."
