"""
Test cases for MediCare Clinic Appointment System.
CSC 1202 - Software Development Project | Coursework 4
Student: 25/U/03324/PSA
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from .models import User, Patient, Doctor, Appointment, MedicalHistory, ContactMessage


class UserRegistrationTest(TestCase):
    """Test patient registration functionality."""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')

    def test_registration_page_loads(self):
        """Registration page should return HTTP 200."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register_patient.html')

    def test_valid_patient_registration(self):
        """Valid registration data should create user and patient profile."""
        data = {
            'username': 'testpatient',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '+256700000000',
            'password1': 'StrongPass@123',
            'password2': 'StrongPass@123',
            'date_of_birth': '1995-05-15',
            'address': 'Kampala, Uganda',
            'blood_group': 'O+',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(User.objects.filter(username='testpatient').count(), 1)
        user = User.objects.get(username='testpatient')
        self.assertTrue(user.is_patient)
        self.assertTrue(Patient.objects.filter(user=user).exists())

    def test_duplicate_username_rejected(self):
        """Duplicate username should fail validation."""
        User.objects.create_user(username='existing', password='pass')
        data = {
            'username': 'existing',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'phone': '+256700000001',
            'password1': 'StrongPass@123',
            'password2': 'StrongPass@123',
            'date_of_birth': '1998-01-01',
            'address': 'Entebbe, Uganda',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(User.objects.filter(username='existing').count(), 1)

    def test_future_dob_rejected(self):
        """Date of birth in the future should be rejected."""
        future_date = (date.today() + timedelta(days=365)).strftime('%Y-%m-%d')
        data = {
            'username': 'futureuser',
            'first_name': 'Future',
            'last_name': 'User',
            'email': 'future@example.com',
            'phone': '+256700000002',
            'password1': 'StrongPass@123',
            'password2': 'StrongPass@123',
            'date_of_birth': future_date,
            'address': 'Jinja, Uganda',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(User.objects.filter(username='futureuser').count(), 0)


class AuthenticationTest(TestCase):
    """Test login/logout functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser', password='TestPass@123', is_patient=True
        )
        self.patient = Patient.objects.create(
            user=self.user,
            date_of_birth='1990-01-01',
            address='Kampala'
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_valid_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'TestPass@123'
        })
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)

    def test_invalid_login(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'WrongPassword'
        })
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_protected_page_redirects_anonymous(self):
        """Unauthenticated users should be redirected from protected pages."""
        response = self.client.get(reverse('my_appointments'))
        self.assertRedirects(response, '/login/?next=/patient/appointments/')

    def test_authenticated_user_accesses_dashboard(self):
        self.client.login(username='testuser', password='TestPass@123')
        response = self.client.get(reverse('patient_dashboard'))
        self.assertEqual(response.status_code, 200)


class AppointmentBookingTest(TestCase):
    """Test appointment booking functionality."""

    def setUp(self):
        self.client = Client()

        # Create patient
        self.patient_user = User.objects.create_user(
            username='patient1', password='Pass@1234', is_patient=True,
            first_name='Alice', last_name='Nakato'
        )
        self.patient = Patient.objects.create(
            user=self.patient_user, date_of_birth='1992-03-10', address='Mbale'
        )

        # Create doctor
        self.doctor_user = User.objects.create_user(
            username='doctor1', password='Pass@1234', is_doctor=True,
            first_name='James', last_name='Okello'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user, specialization='General Practice',
            available_days='Mon,Tue,Wed,Thu,Fri'
        )

        self.future_date = (date.today() + timedelta(days=3)).strftime('%Y-%m-%d')

    def test_booking_page_requires_login(self):
        response = self.client.get(reverse('book_appointment'))
        self.assertEqual(response.status_code, 302)

    def test_valid_appointment_booking(self):
        self.client.login(username='patient1', password='Pass@1234')
        response = self.client.post(reverse('book_appointment'), {
            'doctor': self.doctor.pk,
            'date': self.future_date,
            'time': '09:00',
            'reason': 'Routine checkup'
        })
        self.assertEqual(Appointment.objects.count(), 1)
        appt = Appointment.objects.first()
        self.assertEqual(appt.status, 'pending')
        self.assertEqual(appt.patient, self.patient)

    def test_double_booking_prevented(self):
        """Same doctor, date, time should not be bookable twice."""
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=self.future_date,
            time='09:00',
            reason='First booking',
            status='approved'
        )
        self.client.login(username='patient1', password='Pass@1234')
        response = self.client.post(reverse('book_appointment'), {
            'doctor': self.doctor.pk,
            'date': self.future_date,
            'time': '09:00',
            'reason': 'Second booking attempt'
        })
        self.assertEqual(Appointment.objects.count(), 1)  # Still only 1

    def test_past_date_booking_rejected(self):
        self.client.login(username='patient1', password='Pass@1234')
        past_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.post(reverse('book_appointment'), {
            'doctor': self.doctor.pk,
            'date': past_date,
            'time': '10:00',
            'reason': 'Past date test'
        })
        self.assertEqual(Appointment.objects.count(), 0)


class DoctorApprovalTest(TestCase):
    """Test doctor appointment management."""

    def setUp(self):
        self.client = Client()
        self.doctor_user = User.objects.create_user(
            username='drsmith', password='Pass@1234', is_doctor=True,
            first_name='Dr', last_name='Smith'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user, specialization='Cardiology',
            available_days='Mon,Tue,Wed'
        )
        patient_user = User.objects.create_user(
            username='pat2', password='Pass@1234', is_patient=True,
            first_name='Bob', last_name='Mutebe'
        )
        self.patient = Patient.objects.create(
            user=patient_user, date_of_birth='1988-07-22', address='Gulu'
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=date.today() + timedelta(days=2),
            time='10:00',
            reason='Heart checkup',
            status='pending'
        )

    def test_approve_changes_status(self):
        self.client.login(username='drsmith', password='Pass@1234')
        self.client.post(reverse('approve_appointment', kwargs={'pk': self.appointment.pk}))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'approved')

    def test_cancel_changes_status(self):
        self.client.login(username='drsmith', password='Pass@1234')
        self.client.post(reverse('cancel_appointment_doctor', kwargs={'pk': self.appointment.pk}))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'cancelled')

    def test_non_doctor_cannot_approve(self):
        """A patient should not be able to approve appointments."""
        patient_user = User.objects.create_user(
            username='hacker', password='Pass@1234', is_patient=True
        )
        Patient.objects.create(user=patient_user, date_of_birth='2000-01-01', address='X')
        self.client.login(username='hacker', password='Pass@1234')
        response = self.client.post(
            reverse('approve_appointment', kwargs={'pk': self.appointment.pk})
        )
        self.appointment.refresh_from_db()
        self.assertNotEqual(self.appointment.status, 'approved')


class ContactFormTest(TestCase):
    """Test contact/feedback form."""

    def test_valid_contact_form_saves(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'general',
            'message': 'This is a test message for the clinic.'
        })
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertRedirects(response, reverse('contact'))

    def test_empty_message_rejected(self):
        response = self.client.post(reverse('contact'), {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'general',
            'message': ''
        })
        self.assertEqual(ContactMessage.objects.count(), 0)
