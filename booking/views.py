"""
Views for MediCare Clinic Appointment System.
CSC 1202 - Software Development Project | Coursework 4
Student: 25/U/03324/PSA
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from functools import wraps

from .models import User, Patient, Doctor, Appointment, MedicalHistory, ContactMessage
from .forms import (
    PatientSignUpForm, DoctorSignUpForm, AppointmentBookingForm,
    AppointmentUpdateForm, MedicalRecordForm, ContactForm, PatientProfileForm
)


# ─────────────────────── Access Decorators ───────────────────────

def patient_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_patient:
            messages.error(request, 'Access denied. This page is for patients only.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped


def doctor_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_doctor:
            messages.error(request, 'Access denied. This page is for doctors only.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ─────────────────────── Public Views ────────────────────────────

def home(request):
    """Public home page."""
    doctors = Doctor.objects.filter(is_available=True).select_related('user')[:6]
    total_doctors = Doctor.objects.count()
    total_patients = Patient.objects.count()
    total_appointments = Appointment.objects.count()
    context = {
        'doctors': doctors,
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
    }
    return render(request, 'booking/home.html', context)


def about(request):
    return render(request, 'booking/about.html')


def doctor_list(request):
    """Public page listing all available doctors."""
    specialization = request.GET.get('specialization', '')
    doctors = Doctor.objects.filter(is_available=True).select_related('user')
    if specialization:
        doctors = doctors.filter(specialization=specialization)
    specializations = Doctor.SPECIALIZATION_CHOICES
    return render(request, 'booking/doctor_list.html', {
        'doctors': doctors,
        'specializations': specializations,
        'selected': specialization,
    })


def contact(request):
    """Public contact/feedback form."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent. We will get back to you shortly!')
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'booking/contact.html', {'form': form})


# ─────────────────────── Auth Views ──────────────────────────────

def register_patient(request):
    """Patient registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('dashboard')
    else:
        form = PatientSignUpForm()
    return render(request, 'registration/register_patient.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')


# ─────────────────────── Dashboard ───────────────────────────────

@login_required
def dashboard(request):
    """Role-based dashboard redirect."""
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    elif request.user.is_doctor:
        return redirect('doctor_dashboard')
    elif request.user.is_patient:
        return redirect('patient_dashboard')
    return redirect('home')


@login_required
@patient_required
def patient_dashboard(request):
    """Patient dashboard showing upcoming appointments and summary."""
    patient = get_object_or_404(Patient, user=request.user)
    upcoming = Appointment.objects.filter(
        patient=patient, date__gte=timezone.now().date()
    ).exclude(status='cancelled').order_by('date', 'time')[:5]
    recent_history = MedicalHistory.objects.filter(patient=patient).order_by('-date')[:3]
    stats = {
        'total': patient.appointments.count(),
        'pending': patient.appointments.filter(status='pending').count(),
        'approved': patient.appointments.filter(status='approved').count(),
        'completed': patient.appointments.filter(status='completed').count(),
    }
    return render(request, 'booking/patient_dashboard.html', {
        'patient': patient,
        'upcoming': upcoming,
        'recent_history': recent_history,
        'stats': stats,
    })


@login_required
@doctor_required
def doctor_dashboard(request):
    """Doctor dashboard."""
    doctor = get_object_or_404(Doctor, user=request.user)
    today_appointments = Appointment.objects.filter(
        doctor=doctor, date=timezone.now().date()
    ).exclude(status='cancelled').select_related('patient__user').order_by('time')
    pending = Appointment.objects.filter(
        doctor=doctor, status='pending'
    ).select_related('patient__user').order_by('date', 'time')[:10]
    stats = {
        'today': today_appointments.count(),
        'pending': doctor.appointments.filter(status='pending').count(),
        'total': doctor.appointments.count(),
        'completed': doctor.appointments.filter(status='completed').count(),
    }
    return render(request, 'booking/doctor_dashboard.html', {
        'doctor': doctor,
        'today_appointments': today_appointments,
        'pending_appointments': pending,
        'stats': stats,
    })


@login_required
def admin_dashboard(request):
    """Admin dashboard (superuser only)."""
    if not request.user.is_superuser:
        return redirect('home')
    stats = {
        'total_patients': Patient.objects.count(),
        'total_doctors': Doctor.objects.count(),
        'total_appointments': Appointment.objects.count(),
        'pending_appointments': Appointment.objects.filter(status='pending').count(),
        'unresolved_messages': ContactMessage.objects.filter(is_resolved=False).count(),
    }
    recent_appointments = Appointment.objects.select_related(
        'patient__user', 'doctor__user'
    ).order_by('-created_at')[:10]
    unresolved_messages = ContactMessage.objects.filter(is_resolved=False).order_by('-created_at')[:5]
    return render(request, 'booking/admin_dashboard.html', {
        'stats': stats,
        'recent_appointments': recent_appointments,
        'unresolved_messages': unresolved_messages,
    })


# ─────────────────────── Appointment Views ───────────────────────

@login_required
@patient_required
def book_appointment(request):
    """Patient books a new appointment."""
    patient = get_object_or_404(Patient, user=request.user)
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.save()
            messages.success(
                request,
                f'Appointment booked with Dr. {appointment.doctor.user.get_full_name()} '
                f'on {appointment.date} at {appointment.get_time_display()}. '
                'Status: Pending approval.'
            )
            return redirect('my_appointments')
    else:
        doctor_id = request.GET.get('doctor')
        initial = {}
        if doctor_id:
            initial['doctor'] = doctor_id
        form = AppointmentBookingForm(initial=initial)
    return render(request, 'booking/book_appointment.html', {'form': form})


@login_required
@patient_required
def my_appointments(request):
    """Patient views their appointment list."""
    patient = get_object_or_404(Patient, user=request.user)
    status_filter = request.GET.get('status', '')
    appointments = patient.appointments.select_related('doctor__user').order_by('-date', '-time')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    return render(request, 'booking/my_appointments.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'STATUS_CHOICES': Appointment.STATUS_CHOICES,
    })


@login_required
@patient_required
def cancel_appointment(request, pk):
    """Patient cancels their own appointment."""
    patient = get_object_or_404(Patient, user=request.user)
    appointment = get_object_or_404(Appointment, pk=pk, patient=patient)
    if appointment.status in ('pending', 'approved'):
        appointment.status = 'cancelled'
        appointment.save()
        messages.success(request, 'Appointment cancelled successfully.')
    else:
        messages.error(request, 'This appointment cannot be cancelled.')
    return redirect('my_appointments')


@login_required
@doctor_required
def doctor_appointments(request):
    """Doctor views all their appointments."""
    doctor = get_object_or_404(Doctor, user=request.user)
    status_filter = request.GET.get('status', 'pending')
    date_filter = request.GET.get('date', '')
    appointments = doctor.appointments.select_related('patient__user').order_by('date', 'time')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    if date_filter:
        appointments = appointments.filter(date=date_filter)
    return render(request, 'booking/doctor_appointments.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'STATUS_CHOICES': Appointment.STATUS_CHOICES,
    })


@login_required
@doctor_required
def approve_appointment(request, pk):
    """Doctor approves a pending appointment."""
    doctor = get_object_or_404(Doctor, user=request.user)
    appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor)
    if request.method == 'POST':
        appointment.status = 'approved'
        appointment.save()
        messages.success(
            request,
            f'Appointment for {appointment.patient.user.get_full_name()} on {appointment.date} approved.'
        )
    return redirect('doctor_appointments')


@login_required
@doctor_required
def cancel_appointment_doctor(request, pk):
    """Doctor cancels an appointment."""
    doctor = get_object_or_404(Doctor, user=request.user)
    appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor)
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        messages.warning(request, f'Appointment cancelled for {appointment.patient.user.get_full_name()}.')
    return redirect('doctor_appointments')


@login_required
@doctor_required
def complete_appointment(request, pk):
    """Doctor marks an appointment as completed."""
    doctor = get_object_or_404(Doctor, user=request.user)
    appointment = get_object_or_404(Appointment, pk=pk, doctor=doctor)
    if request.method == 'POST':
        appointment.status = 'completed'
        notes = request.POST.get('notes', '')
        if notes:
            appointment.notes = notes
        appointment.save()
        messages.success(request, 'Appointment marked as completed.')
    return redirect('doctor_appointments')


# ─────────────────────── Medical History ─────────────────────────

@login_required
@patient_required
def patient_history(request):
    """Patient views their medical history."""
    patient = get_object_or_404(Patient, user=request.user)
    records = patient.medical_history.select_related('doctor__user').order_by('-date')
    return render(request, 'booking/medical_history.html', {
        'patient': patient,
        'records': records,
    })


@login_required
@doctor_required
def add_medical_record(request, patient_id):
    """Doctor adds a medical history record for a patient."""
    patient = get_object_or_404(Patient, pk=patient_id)
    doctor = get_object_or_404(Doctor, user=request.user)
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = patient
            record.doctor = doctor
            record.save()
            messages.success(request, f'Medical record added for {patient.user.get_full_name()}.')
            return redirect('doctor_appointments')
    else:
        form = MedicalRecordForm()
    return render(request, 'booking/add_medical_record.html', {
        'form': form,
        'patient': patient,
    })


@login_required
@doctor_required
def doctor_patient_list(request):
    """Doctor sees list of their patients."""
    doctor = get_object_or_404(Doctor, user=request.user)
    patient_ids = doctor.appointments.filter(
        status__in=['approved', 'completed']
    ).values_list('patient_id', flat=True).distinct()
    patients = Patient.objects.filter(id__in=patient_ids).select_related('user')
    return render(request, 'booking/doctor_patient_list.html', {'patients': patients})


# ─────────────────────── Profile ─────────────────────────────────

@login_required
@patient_required
def patient_profile(request):
    """Patient edits their profile."""
    patient = get_object_or_404(Patient, user=request.user)
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=patient)
        if form.is_valid():
            patient = form.save(commit=False)
            user = request.user
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.email = form.cleaned_data.get('email', user.email)
            user.phone = form.cleaned_data.get('phone', user.phone)
            user.save()
            patient.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('patient_dashboard')
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': request.user.phone,
        }
        form = PatientProfileForm(instance=patient, initial=initial)
    return render(request, 'booking/patient_profile.html', {'form': form})
