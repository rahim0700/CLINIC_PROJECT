"""
Django Admin configuration for MediCare Clinic System.
CSC 1202 - Software Development Project | Coursework 4
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Patient, Doctor, Appointment, MedicalHistory, ContactMessage


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'is_patient', 'is_doctor', 'is_superuser']
    list_filter = ['is_patient', 'is_doctor', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('is_patient', 'is_doctor', 'phone')}),
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['user', 'date_of_birth', 'blood_group', 'emergency_contact', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    list_filter = ['blood_group']


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'available_days', 'consultation_fee', 'is_available']
    list_filter = ['specialization', 'is_available']
    search_fields = ['user__first_name', 'user__last_name']
    list_editable = ['is_available']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'date', 'time', 'status', 'created_at']
    list_filter = ['status', 'date', 'doctor__specialization']
    search_fields = ['patient__user__first_name', 'patient__user__last_name', 'doctor__user__first_name']
    list_editable = ['status']
    date_hierarchy = 'date'


@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'date', 'created_at']
    list_filter = ['date']
    search_fields = ['patient__user__first_name', 'diagnosis']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'is_resolved']
    list_filter = ['is_resolved', 'subject']
    list_editable = ['is_resolved']
    search_fields = ['name', 'email', 'message']


# Customize admin site headers
admin.site.site_header = 'MediCare Clinic Administration'
admin.site.site_title = 'MediCare Admin'
admin.site.index_title = 'Clinic Management Dashboard'
