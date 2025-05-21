from .auth_views import LoginView, SignUpView
from .profile_views import ProfileViewSet, ProfileUpdateView
from .doctor_views import DoctorProfileView, DoctorAvailabilityViewSet, FavoriteDoctorViewSet, DoctorDetailView
from .appointment_views import AppointmentViewSet, PrescriptionViewSet
from .notification_views import NotificationViewSet

__all__ = [
    'LoginView',
    'SignUpView',
    'ProfileViewSet',
    'ProfileUpdateView',
    'DoctorProfileView',
    'DoctorAvailabilityViewSet',
    'AppointmentViewSet',
    'PrescriptionViewSet',
    'FavoriteDoctorViewSet',
    'NotificationViewSet',
    'DoctorDetailView',
]