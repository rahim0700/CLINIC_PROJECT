"""
Database Models for MediCare Clinic Appointment System.
CSC 1202 - Software Development Project | Coursework 4
Student: 25/U/03324/PSA
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Extended user model with role flags."""
    is_patient = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    def get_role(self):
        if self.is_superuser:
            return 'Admin'
        elif self.is_doctor:
            return 'Doctor'
        elif self.is_patient:
            return 'Patient'
        return 'Unknown'


class Patient(models.Model):
    """Patient profile linked to User."""
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField()
    address = models.TextField()
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    allergies = models.TextField(blank=True, help_text="List any known allergies")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'

    def __str__(self):
        return f"Patient: {self.user.get_full_name()}"

    def get_age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class Doctor(models.Model):
    """Doctor profile linked to User."""
    SPECIALIZATION_CHOICES = [
        ('General Practice', 'General Practice'),
        ('Cardiology', 'Cardiology'),
        ('Dermatology', 'Dermatology'),
        ('Neurology', 'Neurology'),
        ('Orthopedics', 'Orthopedics'),
        ('Pediatrics', 'Pediatrics'),
        ('Gynecology', 'Gynecology'),
        ('Ophthalmology', 'Ophthalmology'),
        ('ENT', 'ENT (Ear, Nose & Throat)'),
        ('Psychiatry', 'Psychiatry'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES)
    available_days = models.CharField(
        max_length=100,
        help_text="Comma-separated e.g. Mon,Tue,Wed",
        default="Mon,Tue,Wed,Thu,Fri"
    )
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=50000.00)
    bio = models.TextField(blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctors'

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} — {self.specialization}"

    def get_available_days_list(self):
        return [day.strip() for day in self.available_days.split(',')]


class Appointment(models.Model):
    """Appointment booking between patient and doctor."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    TIME_SLOTS = [
        ('08:00', '8:00 AM'),
        ('08:30', '8:30 AM'),
        ('09:00', '9:00 AM'),
        ('09:30', '9:30 AM'),
        ('10:00', '10:00 AM'),
        ('10:30', '10:30 AM'),
        ('11:00', '11:00 AM'),
        ('11:30', '11:30 AM'),
        ('14:00', '2:00 PM'),
        ('14:30', '2:30 PM'),
        ('15:00', '3:00 PM'),
        ('15:30', '3:30 PM'),
        ('16:00', '4:00 PM'),
        ('16:30', '4:30 PM'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.CharField(max_length=5, choices=TIME_SLOTS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(help_text="Describe your symptoms or reason for visit")
    notes = models.TextField(blank=True, help_text="Doctor's notes (filled after appointment)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        ordering = ['-date', '-time']
        unique_together = ['doctor', 'date', 'time']

    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.date} at {self.time}"

    def get_status_badge(self):
        badges = {
            'pending': 'warning',
            'approved': 'success',
            'cancelled': 'danger',
            'completed': 'primary',
        }
        return badges.get(self.status, 'secondary')


class MedicalHistory(models.Model):
    """Medical records for a patient, created by a doctor."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_history')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='records_written')
    appointment = models.OneToOneField(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='medical_record'
    )
    diagnosis = models.TextField()
    prescription = models.TextField()
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Medical History Record'
        verbose_name_plural = 'Medical History Records'
        ordering = ['-date']

    def __str__(self):
        return f"Record for {self.patient} on {self.date}"


class ContactMessage(models.Model):
    """Feedback and contact form submissions."""
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('appointment', 'Appointment Issue'),
        ('billing', 'Billing Question'),
        ('feedback', 'Feedback / Suggestion'),
        ('complaint', 'Complaint'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, default='general')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_messages'
    )

    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name} — {self.get_subject_display()}"
