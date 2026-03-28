# NIT ID Card Portal

A complete Django-based Student ID Card Generator for **Naresh i Technologies**.  
Students submit a payment receipt for verification; admins approve and auto-generate a
professional CR80-sized ID card (PNG + PDF) with QR code.

---

## Screenshots / Flow

```
Student Portal            Admin Panel
──────────────            ───────────
Home Page           →     Admin Login
Apply for ID Card   →     Dashboard (stats + table)
  (photo + receipt)       Review Request
Track Status        →       ├── View receipt image
Download Card       ←       ├── Edit card details
                            ├── Approve / Reject
                            ├── Generate Card (PNG + PDF)
                            └── Download Card
```

---

## Quick Start — Docker (Recommended)

### Prerequisites
- Docker Desktop (or Docker Engine + Docker Compose)

### Steps

```bash
# 1. Clone / unzip the project
cd idcard_project

# 2. Start (builds image, runs migrations, creates admin user)
docker compose up --build
```

The server will be available at **http://localhost:8000**

Default admin credentials (created automatically):
| Username | Password |
|----------|----------|
| `admin`  | `admin123` |

> ⚠️ Change the password immediately via http://localhost:8000/admin/

---

## Quick Start — Local Python (Without Docker)

### Prerequisites
- Python 3.10+
- pip

### Steps

```bash
# 1. Navigate to project folder
cd idcard_project

# 2. Run the automated setup script
chmod +x setup.sh
./setup.sh

# 3. Start the development server
source venv/bin/activate
python manage.py runserver
```

Or manually:

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env              # Edit .env if needed

python manage.py migrate

python manage.py createsuperuser  # Follow prompts

python manage.py runserver
```

---

## URLs

| URL | Description |
|-----|-------------|
| `http://localhost:8000/` | Student home page |
| `http://localhost:8000/submit/` | Apply for ID card |
| `http://localhost:8000/track/` | Track by roll number |
| `http://localhost:8000/status/<id>/` | View request status |
| `http://localhost:8000/login/` | Admin login |
| `http://localhost:8000/admin-panel/` | Admin dashboard |
| `http://localhost:8000/admin/` | Django built-in admin |

---

## Project Structure

```
idcard_project/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── setup.sh
├── .env                        ← your config (gitignored)
├── .env.example                ← safe template to commit
│
├── idcard_project/             ← Django project package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── idcard_app/                 ← Main application
│   ├── models.py               ← IDCardRequest model
│   ├── views.py                ← All views (student + admin)
│   ├── urls.py                 ← URL routing
│   ├── forms.py                ← Student & admin forms
│   ├── admin.py                ← Django admin registration
│   ├── card_generator.py       ← PNG + PDF ID card generator
│   ├── migrations/
│   │   └── 0001_initial.py
│   └── templates/
│       └── idcard_app/
│           ├── base.html
│           ├── home.html
│           ├── submit_request.html
│           ├── track_status.html
│           ├── track_by_roll.html
│           ├── login.html
│           ├── admin_dashboard.html
│           └── admin_view_request.html
│
└── media/                      ← Uploaded & generated files
    ├── photos/                 ← Student passport photos
    ├── receipts/               ← Payment receipt images
    └── generated_cards/        ← Generated PNG + PDF cards
```

---

## System Workflow

```
1. Student pays ₹100 at reception → gets paper receipt
2. Student visits /submit/ → fills form, uploads photo + receipt
3. Admin logs in at /login/ → visits dashboard
4. Admin opens request → views receipt image
5. Admin edits confirmed card details (name, course, roll, batch)
6. Admin sets status = Approved → saves
7. Admin clicks "Generate ID Card" button
8. System creates PNG (CR80 @ 300 DPI) + PDF automatically
9. Student downloads card at /status/<id>/
```

---

## ID Card Specification

| Property | Value |
|----------|-------|
| Size | CR80 (85.6 mm × 54 mm) |
| Resolution | 300 DPI |
| Formats | PNG + PDF |
| Layout | NIT red/yellow branding |
| Photo | Passport-size inset |
| QR Code | Encoded name, roll, course |
| Fields | Name, Course, Batch, Roll No, Issue Date, Valid Till |

---

## Environment Variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | insecure-dev-key | Django secret key — **change in production** |
| `DEBUG` | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated list |
| `INSTITUTE_NAME` | Naresh i Technologies | Shown on cards & footer |
| `INSTITUTE_ADDRESS` | … | Shown in footer |
| `INSTITUTE_PHONE` | 040 2374 6666 | Shown in footer |
| `INSTITUTE_EMAIL` | info@nareshit.com | Shown in footer |
| `INSTITUTE_WEBSITE` | www.nareshit.com | Shown in footer |

---

## Admin Panel Features

- **Dashboard** — Stats (total/pending/approved/generated/rejected) + paginated table
- **Search & Filter** — by name, roll number, course, email, and status
- **Quick Actions** — Approve or reject directly from the table row
- **Detail View** — Full student info, receipt image viewer, editable card fields
- **Generate Card** — One-click PNG + PDF generation after approval
- **Download** — Download PNG or PDF from both admin panel and student portal

---

## Security Notes

Before going to production:
1. Set `DEBUG=False` in `.env`
2. Change `SECRET_KEY` to a long random string
3. Change admin password from `admin123`
4. Add your domain to `ALLOWED_HOSTS`
5. Use a proper web server (gunicorn + nginx) instead of `runserver`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Django 4.2 |
| Database | SQLite (default) |
| Image Processing | Pillow |
| PDF Generation | ReportLab |
| QR Code | qrcode |
| Frontend | Bootstrap 5.3, Bootstrap Icons |
| Fonts | Google Fonts (Rajdhani + Inter) |
| Config | python-decouple |
| Static Files | WhiteNoise |
| Container | Docker + Docker Compose |

---

## Troubleshooting

**"No module named 'decouple'"** → Run `pip install -r requirements.txt`

**Images not loading** → Ensure `MEDIA_ROOT` directory exists and is writable:
```bash
mkdir -p media/photos media/receipts media/generated_cards
```

**Card generation fails** → Check that DejaVu fonts are installed:
```bash
# Ubuntu/Debian
sudo apt-get install fonts-dejavu-core
# Or the generator will fall back to PIL default font
```

**Port 8000 already in use** → Change port in `docker-compose.yml` from `"8000:8000"` to e.g. `"8080:8000"`
