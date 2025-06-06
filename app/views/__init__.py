from .auth_views import LoginView, SignUpView
from .profile_views import ProfileViewSet, ProfileUpdateView
from .doctor_views import DoctorProfileView, DoctorAvailabilityViewSet, FavoriteDoctorViewSet , DoctorAvailabilityView
from .appointment_views import AppointmentViewSet, AppointmentsView
from .notification_views import NotificationViewSet
from .prescription_views import PrescriptionViewSet, DoctorPrescriptionsView
from .availability_views import DoctorAvailabilityManagementView
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
    'DoctorAvailabilityView',
    'AppointmentsView',
    'DoctorPrescriptionsView',
    'DoctorAvailabilityManagementView'
]