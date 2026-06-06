# MediCare Clinic Management System
**CSC 1202 — Software Development Project | Coursework 4**  
**Student:** 25/U/03324/PSA | Makerere University | 2026

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py makemigrations
python manage.py migrate

# 3. Create superuser (admin)
python manage.py createsuperuser

# 4. Run development server
python manage.py runserver
```

Visit: http://127.0.0.1:8000

## Deployment (PythonAnywhere)
1. Upload zip and extract
2. Create virtualenv and install requirements
3. Set `DEBUG = False` and `SECRET_KEY` from environment
4. Run `python manage.py collectstatic`
5. Configure WSGI file to point to `clinic_system.wsgi`

## Features
- Patient registration and login
- Appointment booking with double-booking prevention
- Doctor schedule viewing and management
- Appointment approval/cancellation/completion workflow
- Admin management dashboard
- Patient medical history records
- Contact/feedback form
- Role-based access control (Patient / Doctor / Admin)
