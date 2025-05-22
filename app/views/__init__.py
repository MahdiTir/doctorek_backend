from .auth_views import LoginView, SignUpView
from .profile_views import ProfileViewSet, ProfileUpdateView
from .doctor_views import DoctorProfileView, DoctorAvailabilityViewSet, FavoriteDoctorViewSet , DoctorAvailabilityView
from .appointment_views import AppointmentViewSet
from .notification_views import NotificationViewSet
from .prescription_views import PrescriptionViewSet

__all__ = [
    'LoginView',
    'SignUpView',
    'ProfileViewSet',
    'ProfileUpdateView',
    'DoctorProfileView',
    'DoctorAvailabilityViewSet',
    'AppointmentViewSet',
    'FavoriteDoctorViewSet',
    'NotificationViewSet',
    'PrescriptionViewSet',
    'DoctorAvailabilityView'
]