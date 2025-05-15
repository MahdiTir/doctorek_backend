from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters import rest_framework as filters


import requests
from django.conf import settings
from django.shortcuts import get_object_or_404

import uuid

from rest_framework.decorators import action

from datetime import datetime
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
    NotificationSerializer,
    
)

from .utils import get_user_id_from_token

from django.conf import settings


class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'detail': 'Email and password are required.'}, status=400)

        response = requests.post(
            f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={
                'apikey': settings.SUPABASE_KEY,
                'Content-Type': 'application/json'
            },
            json={'email': email, 'password': password}
        )

        if response.status_code == 200:
            return Response(response.json())  
        else:
            return Response(response.json(), status=response.status_code)


class SignUpView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user_type = request.data.get("user_type") 

        if not email or not password:
            return Response({"detail": "Email and password are required."}, status=400)

        payload = {
            "email": email,
            "password": password,
        }

        if user_type:
            payload["data"] = {"user_type": user_type}

        response = requests.post(
            f"{settings.SUPABASE_URL}/auth/v1/signup",
            headers={
                "apikey": settings.SUPABASE_KEY,
                "Content-Type": "application/json"
            },
            json=payload
        )

        if response.status_code != 200:
            return Response(response.json(), status=response.status_code)
        
        
        user = response.json().get("user")
        if not user:
            return Response({"detail": "User created but no user data returned."}, status=500)

        user_id = user["id"]

        if user_type:
            patch = requests.patch(
                f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}",
                headers={
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                },
                json={"user_type": user_type}
            )

            if patch.status_code not in (200, 204):
                return Response({
                    "detail": "User created but failed to update user_type in profile.",
                    "error": patch.json()
                }, status=500)

        return Response({"user": user}, status=201)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profiles.objects.all()
    serializer_class = ProfileSerializer
    #permission_classes = [IsAuthenticated]


class ProfileUpdateView(APIView):
    def patch(self, request):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)  
        try:
            profile = Profiles.objects.get(id=user_id)
        except Profiles.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorProfileViewSet(viewsets.ModelViewSet):
    queryset = DoctorProfiles.objects.all()
    serializer_class = DoctorProfileSerializer
    #permission_classes = [IsAuthenticated]

    
    def create(self, request):
        
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = Profiles.objects.get(id=user_id)
        except Profiles.DoesNotExist:
            return Response({"detail": "User profile not found"}, status=status.HTTP_404_NOT_FOUND)

        doctor_id = uuid.uuid4()
        print(" Debug loggeduser .id:",user.id)
        print(" Debug user_id:",user_id)
        
        data = {
            #**request.data,
            'id': doctor_id,
            'user_id': user_id,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

        # Add all other fields from request.data
        for key, value in request.data.items():
            if key not in data:
                data[key] = value
            # Print debug information
        print("Debug - Data being sent to serializer:", data)
        print("Debug - User ID:", user.id)

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print("Debug - Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
    
