from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from ..utils import get_user_id_from_token
from datetime import datetime


from ..models import (
    Profiles,
    DoctorProfiles,
    DoctorAvailability,
    FavoriteDoctors,
)
from ..serializers import (
    DoctorProfileSerializer,
    DoctorAvailabilitySerializer,
    FavoriteDoctorSerializer,
    DoctorDetailSerializer
)

import uuid

class DoctorProfileView(APIView):
    queryset = DoctorProfiles.objects.all()
    serializer_class = DoctorProfileSerializer

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
    

class DoctorDetailView(APIView):
    def get(self, request, doctor_id=None):
        """
        Get detailed information for a specific doctor including availability and profile information
        """
        # Get doctor ID either from URL path or query parameters
        if not doctor_id:
            doctor_id = request.query_params.get('id')
            
        if not doctor_id:
            return Response({"detail": "Doctor ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get authenticated user (optional, can be removed if no auth needed for this endpoint)
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Try to fetch the doctor with the given ID
        try:
            doctor = DoctorProfiles.objects.select_related('user').get(user_id=doctor_id)
        except DoctorProfiles.DoesNotExist:
            return Response({"detail": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize the doctor data with our detailed serializer
        serializer = DoctorDetailSerializer(doctor)
        return Response(serializer.data)
    

    
    
    

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