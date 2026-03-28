@echo off
echo.
echo ======================================================
echo   Naresh i Technologies - ID Card Portal Setup
echo ======================================================
echo.

echo [1/6] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [2/6] Activating virtual environment...
call venv\Scripts\activate

echo [3/6] Installing dependencies...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo [4/6] Running database migrations...
python manage.py migrate

echo [5/6] Creating default admin user...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@nareshit.com', 'admin123'); print('Admin user ready: admin / admin123')"

echo [6/6] Collecting static files...
python manage.py collectstatic --noinput -v 0

echo.
echo ======================================================
echo   Setup complete!
echo ======================================================
echo.
echo   To start the server, run:
echo     venv\Scripts\activate
echo     python manage.py runserver
echo.
echo   Then open: http://127.0.0.1:8000/
echo.
echo   Admin Panel : http://127.0.0.1:8000/admin-panel/
echo   Username    : admin
echo   Password    : admin123
echo.
pause
