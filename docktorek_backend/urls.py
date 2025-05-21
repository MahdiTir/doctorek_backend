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

from app.views import LoginView, SignUpView, ProfileViewSet , ProfileUpdateView, DoctorProfileView, DoctorAvailabilityViewSet, AppointmentViewSet, PrescriptionViewSet, FavoriteDoctorViewSet, NotificationViewSet 

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.views import (
    ProfileViewSet,
    DoctorProfileView,
    DoctorAvailabilityViewSet,
    AppointmentViewSet,
    PrescriptionViewSet,
    FavoriteDoctorViewSet,
    NotificationViewSet,
    ProfileUpdateView,
    LoginView,
    SignUpView,
    DoctorDetailView
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
    path('api/doctors/<uuid:doctor_id>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('api/doctor-detail/', DoctorDetailView.as_view(), name='doctor-detail-query'),  
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/signup/', SignUpView.as_view(), name='signup'),
]

