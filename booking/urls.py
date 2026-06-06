"""
URL Configuration for the booking app.
CSC 1202 - Software Development Project | Coursework 4
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('contact/', views.contact, name='contact'),

    # Authentication
    path('register/', views.register_patient, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard (role-based redirect)
    path('dashboard/', views.dashboard, name='dashboard'),

    # Patient views
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/book/', views.book_appointment, name='book_appointment'),
    path('patient/appointments/', views.my_appointments, name='my_appointments'),
    path('patient/appointments/cancel/<int:pk>/', views.cancel_appointment, name='cancel_appointment'),
    path('patient/history/', views.patient_history, name='history'),
    path('patient/profile/', views.patient_profile, name='patient_profile'),

    # Doctor views
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/appointments/approve/<int:pk>/', views.approve_appointment, name='approve_appointment'),
    path('doctor/appointments/cancel/<int:pk>/', views.cancel_appointment_doctor, name='cancel_appointment_doctor'),
    path('doctor/appointments/complete/<int:pk>/', views.complete_appointment, name='complete_appointment'),
    path('doctor/patients/', views.doctor_patient_list, name='doctor_patient_list'),
    path('doctor/patients/<int:patient_id>/add-record/', views.add_medical_record, name='add_medical_record'),

    # Admin dashboard
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
]
