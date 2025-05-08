from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import (
    Profiles,
    DoctorProfiles,
    DoctorAvailability,
    Appointments,
    Prescriptions,
    FavoriteDoctors,
    Notifications
)
from .serializers import (
    ProfileSerializer,
    DoctorProfileSerializer,
    DoctorAvailabilitySerializer,
    AppointmentSerializer,
    PrescriptionSerializer,
    FavoriteDoctorSerializer,
    NotificationSerializer
)

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profiles.objects.all()
    serializer_class = ProfileSerializer
    #permission_classes = [IsAuthenticated]

class DoctorProfileViewSet(viewsets.ModelViewSet):
    queryset = DoctorProfiles.objects.all()
    serializer_class = DoctorProfileSerializer
    #permission_classes = [IsAuthenticated]

class DoctorAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = DoctorAvailability.objects.all()
    serializer_class = DoctorAvailabilitySerializer
    #permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = DoctorAvailability.objects.all()
        doctor_id = self.request.query_params.get('doctor', None)
        if doctor_id is not None:
            queryset = queryset.filter(doctor_id=doctor_id)
        return queryset

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointments.objects.all()
    serializer_class = AppointmentSerializer
    #permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Appointments.objects.all()
        patient_id = self.request.query_params.get('patient', None)
        doctor_id = self.request.query_params.get('doctor', None)
        if patient_id is not None:
            queryset = queryset.filter(patient_id=patient_id)
        if doctor_id is not None:
            queryset = queryset.filter(doctor_id=doctor_id)
        return queryset

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescriptions.objects.all()
    serializer_class = PrescriptionSerializer
    #permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Prescriptions.objects.all()
        patient_id = self.request.query_params.get('patient', None)
        doctor_id = self.request.query_params.get('doctor', None)
        if patient_id is not None:
            queryset = queryset.filter(patient_id=patient_id)
        if doctor_id is not None:
            queryset = queryset.filter(doctor_id=doctor_id)
        return queryset

class FavoriteDoctorViewSet(viewsets.ModelViewSet):
    queryset = FavoriteDoctors.objects.all()
    serializer_class = FavoriteDoctorSerializer
    #permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = FavoriteDoctors.objects.all()
        patient_id = self.request.query_params.get('patient', None)
        if patient_id is not None:
            queryset = queryset.filter(patient_id=patient_id)
        return queryset

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notifications.objects.all()
    serializer_class = NotificationSerializer
    #permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notifications.objects.all()
        user_id = self.request.query_params.get('user', None)
        if user_id is not None:
            queryset = queryset.filter(user_id=user_id)
        return queryset