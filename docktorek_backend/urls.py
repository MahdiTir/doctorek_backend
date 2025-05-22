"""
URL configuration for docktorek_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from app.views import *
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.views import (
    ProfileViewSet,
    DoctorProfileView,
    DoctorAvailabilityViewSet,
    AppointmentViewSet,
    FavoriteDoctorViewSet,
    NotificationViewSet,
    ProfileUpdateView,
    LoginView,
    SignUpView,
    PrescriptionViewSet,
    DoctorAvailabilityView,
    AppointmentsView,
    DoctorPrescriptionsView,
    DoctorAvailabilityManagementView
    
)

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet)
router.register(r'availability', DoctorAvailabilityViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'prescriptions', PrescriptionViewSet)
router.register(r'favorites', FavoriteDoctorViewSet)
router.register(r'notifications', NotificationViewSet)





urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/profile/', ProfileUpdateView.as_view(), name='my-profile-update'),
    path('api/doctors/', DoctorProfileView.as_view(), name='doctor-profiles'),
    path('api/doctors/<uuid:doctor_id>/', DoctorProfileView.as_view(), name='doctor-detail'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/signup/', SignUpView.as_view(), name='signup'),
    path('api/doctor-availability/', DoctorAvailabilityView.as_view(), name='doctor-availability'),
    path('api/doctor-appointments/', AppointmentsView.as_view(), name='doctor-appointments'),
    path('api/doctor-appointments/<uuid:appointment_id>/', AppointmentsView.as_view(), name='update-appointment-status'),
    path('api/doctor/prescriptions/', DoctorPrescriptionsView.as_view(), name='doctor-prescriptions'),
    path('api/doctor/availability/', DoctorAvailabilityManagementView.as_view(), name='doctor-availability-management'),
    path('api/doctor/availability/<uuid:availability_id>/', DoctorAvailabilityManagementView.as_view(), name='doctor-availability-detail'),

]

