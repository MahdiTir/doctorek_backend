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


class DoctorProfileView(APIView):
    queryset = DoctorProfiles.objects.all()
    serializer_class = DoctorProfileSerializer

    def get(self, request):
        """
        Get doctor profiles ordered by average rating with related profile information
        """

        doctor_id = request.query_params.get('id')
        
        # If doctor_id is provided, return detailed view
        if doctor_id:
            return self.get_doctor_detail(request)
            
        user_id = get_user_id_from_token(request)
        if not user_id or user_id is None:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        print("Debug - Inside get_top_doctors method")
        # Get doctor profiles with related profile data
        doctor_profiles = DoctorProfiles.objects.select_related('user').all()
        
        # Order by average rating in descending order
        doctor_profiles = doctor_profiles.order_by('-average_rating')
        
        # Create custom response data with the requested fields
        result = []
        for doctor in doctor_profiles:

            available_days = DoctorAvailability.objects.filter(
                doctor_id=doctor.id,
                is_available=True
            ).values('day_of_week', 'start_time', 'end_time', 'slot_duration')
            
            doctor_data = {
                'id': doctor.id,
                'specialty': doctor.specialty,
                'hospital_name': doctor.hospital_name,
                'hospital_address': doctor.hospital_address,
                'location': {
                    'lat': doctor.location_lat,
                    'lng': doctor.location_lng
                },
                'average_rating': doctor.average_rating,
                'profiles': {
                    'full_name': doctor.user.full_name if doctor.user else None,
                    'email': doctor.user.email if doctor.user else None,
                    'phone_number': doctor.user.phone_number if doctor.user else None,
                    'avatar_url': doctor.user.avatar_url if doctor.user else None
                },
                'availability': list(available_days)  
        
            }
            result.append(doctor_data)
        
        return Response(result)
    
    def get_doctor_detail(self, request):
        """
        Get detailed information for a specific doctor including availability and profile information
        """
        doctor_id = request.query_params.get('id')
        if not doctor_id:
            return Response({"detail": "Doctor ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get authenticated user (optional, can be removed if no auth needed for this endpoint)
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Try to fetch the doctor with the given ID
        try:
            doctor = DoctorProfiles.objects.select_related('user').get(id=doctor_id)
        except DoctorProfiles.DoesNotExist:
            return Response({"detail": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get available days for this doctor
        available_days = DoctorAvailability.objects.filter(
            doctor_id=doctor_id,
            is_available=True
        ).values('day_of_week', 'is_available')
        
        # Build the response with the same structure as the Supabase query
        result = {
            'id': doctor.id,
            'user_id': doctor.user_id,
            'specialty': doctor.specialty,
            'hospital_name': doctor.hospital_name,
            'hospital_address': doctor.hospital_address,
            'location':{
                'lat': doctor.location_lat,
                'lng': doctor.location_lng
            },
            'bio': doctor.bio,
            'years_of_experience': doctor.years_of_experience,
            'contact_information': doctor.contact_information,
            'average_rating': doctor.average_rating,
            'created_at': doctor.created_at,
            'updated_at': doctor.updated_at,
            'doctor_availability': list(available_days),
            'profiles': {
                'full_name': doctor.user.full_name if doctor.user else None,
                'email': doctor.user.email if doctor.user else None,
                'phone_number': doctor.user.phone_number if doctor.user else None,
                'address': doctor.user.address if doctor.user else None,
                'avatar_url': doctor.user.avatar_url if doctor.user else None
            }
        }
        
        return Response(result)
    

    
    
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
            'user': user_id,
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
    
