"""
Forms for MediCare Clinic Appointment System.
CSC 1202 - Software Development Project | Coursework 4
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from datetime import date
from .models import User, Patient, Doctor, Appointment, MedicalHistory, ContactMessage


class PatientSignUpForm(UserCreationForm):
    """Registration form for patients."""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    blood_group = forms.ChoiceField(choices=[('', '--- Select ---')] + Patient.BLOOD_GROUP_CHOICES, required=False)
    emergency_contact = forms.CharField(max_length=15, required=False)
    allergies = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.is_patient = True
        if commit:
            user.save()
            Patient.objects.create(
                user=user,
                date_of_birth=self.cleaned_data['date_of_birth'],
                address=self.cleaned_data['address'],
                blood_group=self.cleaned_data.get('blood_group', ''),
                emergency_contact=self.cleaned_data.get('emergency_contact', ''),
                allergies=self.cleaned_data.get('allergies', ''),
            )
        return user

    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        if dob >= date.today():
            raise forms.ValidationError("Date of birth must be in the past.")
        return dob


class DoctorSignUpForm(UserCreationForm):
    """Registration form for doctors (admin use)."""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    specialization = forms.ChoiceField(choices=Doctor.SPECIALIZATION_CHOICES)
    available_days = forms.CharField(
        max_length=100,
        initial='Mon,Tue,Wed,Thu,Fri',
        help_text='Comma-separated: Mon,Tue,Wed,Thu,Fri'
    )
    consultation_fee = forms.DecimalField(max_digits=8, decimal_places=2, initial=50000)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    years_of_experience = forms.IntegerField(min_value=0, initial=0)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.is_doctor = True
        if commit:
            user.save()
            Doctor.objects.create(
                user=user,
                specialization=self.cleaned_data['specialization'],
                available_days=self.cleaned_data['available_days'],
                consultation_fee=self.cleaned_data['consultation_fee'],
                bio=self.cleaned_data.get('bio', ''),
                years_of_experience=self.cleaned_data.get('years_of_experience', 0),
            )
        return user


class AppointmentBookingForm(forms.ModelForm):
    """Form for patients to book appointments."""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': str(date.today())}),
        label='Appointment Date'
    )

    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe your symptoms or reason for visit...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = Doctor.objects.filter(is_available=True).select_related('user')
        self.fields['doctor'].label_from_instance = lambda obj: f"Dr. {obj.user.get_full_name()} — {obj.specialization}"

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appt_date = cleaned_data.get('date')
        time = cleaned_data.get('time')

        if appt_date and appt_date < date.today():
            raise forms.ValidationError("Appointment date cannot be in the past.")

        if doctor and appt_date and time:
            # Check for double-booking
            if Appointment.objects.filter(
                doctor=doctor, date=appt_date, time=time
            ).exclude(status='cancelled').exists():
                raise forms.ValidationError(
                    f"Dr. {doctor.user.get_full_name()} already has an appointment at that time. "
                    "Please choose a different time slot."
                )
        return cleaned_data


class AppointmentUpdateForm(forms.ModelForm):
    """Form for doctors to add notes to an appointment."""
    class Meta:
        model = Appointment
        fields = ['notes', 'status']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
        }


class MedicalRecordForm(forms.ModelForm):
    """Form for doctors to create medical history records."""
    follow_up_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )

    class Meta:
        model = MedicalHistory
        fields = ['diagnosis', 'prescription', 'date', 'notes', 'follow_up_date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'prescription': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ContactForm(forms.ModelForm):
    """Public contact/feedback form."""
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write your message here...'}),
            'phone': forms.TextInput(attrs={'placeholder': '+256 700 000000'}),
        }


class PatientProfileForm(forms.ModelForm):
    """Form for patients to update their profile."""
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = Patient
        fields = ['date_of_birth', 'address', 'blood_group', 'emergency_contact', 'allergies']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'allergies': forms.Textarea(attrs={'rows': 2}),
        }
