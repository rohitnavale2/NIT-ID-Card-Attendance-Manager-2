#!/bin/bash
# ============================================================
# NIT ID Card Portal — Quick Setup Script
# ============================================================

set -e

echo ""
echo "======================================================"
echo "  Naresh i Technologies — ID Card Portal Setup"
echo "======================================================"
echo ""

# 1. Create virtual environment
echo "[1/6] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
echo "[2/6] Installing Python dependencies..."
pip install -r requirements.txt -q

# 3. Copy .env if not exists
if [ ! -f .env ]; then
  echo "[3/6] Creating .env from example..."
  cp .env.example .env
  echo "      ⚠️  Edit .env to set your SECRET_KEY and institute details."
else
  echo "[3/6] .env already exists, skipping..."
fi

# 4. Run migrations
echo "[4/6] Running database migrations..."
python manage.py migrate

# 5. Create superuser
echo "[5/6] Creating default admin user..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@nareshit.com', 'admin123')
    print('      ✅ Admin user created: admin / admin123')
else:
    print('      ✅ Admin user already exists')
"

# 6. Collect static files
echo "[6/6] Collecting static files..."
python manage.py collectstatic --noinput -v 0

echo ""
echo "======================================================"
echo "  ✅  Setup complete!"
echo "======================================================"
echo ""
echo "  Start the server:"
echo "    source venv/bin/activate"
echo "    python manage.py runserver"
echo ""
echo "  URLs:"
echo "    Student Portal : http://127.0.0.1:8000/"
echo "    Admin Panel    : http://127.0.0.1:8000/admin-panel/"
echo "    Django Admin   : http://127.0.0.1:8000/admin/"
echo ""
echo "  Default admin credentials:"
echo "    Username : admin"
echo "    Password : admin123"
echo ""
echo "  ⚠️  Change the admin password before deploying to production!"
echo ""
