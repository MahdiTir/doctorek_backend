from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from ..utils import get_user_id_from_token
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from django.utils import timezone
from django.db.models import Q


from ..models import (
    Profiles,
    DoctorProfiles,
    DoctorAvailability,
    FavoriteDoctors,
    Appointments
    
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

    def post(self, request):
        """Create a new doctor profile"""
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Get the user profile
            user = Profiles.objects.get(id=user_id)
            
            # Verify that the user is a doctor
            if user.user_type != Profiles.UserType.DOCTOR:
                return Response({"detail": "Only doctors can create doctor profiles"}, 
                            status=status.HTTP_403_FORBIDDEN)

            # Check if doctor profile already exists
            existing_profile = DoctorProfiles.objects.filter(user_id=user_id).first()
            if existing_profile:
                return Response({
                    "detail": "Doctor profile already exists for this user"
                }, status=status.HTTP_400_BAD_REQUEST)

            
            
            # Create doctor profile data
            data = {
                'id': uuid.uuid4(),
                #'user': user.id,  
                'user_id': user_id, 
                'specialty': request.data.get('specialty'),
                'hospital_name': request.data.get('hospital_name'),
                'hospital_address': request.data.get('hospital_address'),
                'bio': request.data.get('bio'),
                'years_of_experience': request.data.get('years_of_experience'),
                'contact_information': request.data.get('contact_information', {}),
            }

            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Profiles.DoesNotExist:
            return Response({"detail": "User profile not found"}, 
                        status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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
    

    def get_doctor_detail(self, request, doctor_id = None):
        """
        Get detailed information for a specific doctor including availability and profile information
        """
        if not doctor_id:
            doctor_id = request.query_params.get('id')
            
        if not doctor_id:
            return Response({"detail": "Doctor ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            doctor = DoctorProfiles.objects.select_related('user').get(id=doctor_id)
            
            # Get doctor's availability
            available_days = DoctorAvailability.objects.filter(
                doctor_id=doctor.id,
                is_available=True
            ).values('day_of_week', 'start_time', 'end_time', 'slot_duration')
            
            # Format response data
            doctor_data = {
                'id': doctor.id,
                'specialty': doctor.specialty,
                'hospital_name': doctor.hospital_name,
                'hospital_address': doctor.hospital_address,
                'location': {
                    'lat': doctor.location_lat,
                    'lng': doctor.location_lng
                },
                'bio': doctor.bio,
                'years_of_experience': doctor.years_of_experience,
                'contact_information': doctor.contact_information,
                'average_rating': doctor.average_rating,
                'profiles': {
                    'full_name': doctor.user.full_name if doctor.user else None,
                    'email': doctor.user.email if doctor.user else None,
                    'phone_number': doctor.user.phone_number if doctor.user else None,
                    'avatar_url': doctor.user.avatar_url if doctor.user else None
                },
                'availability': list(available_days)
            }
            
            return Response(doctor_data)
            
        except DoctorProfiles.DoesNotExist:
            return Response({"detail": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)
    

    

class DoctorDetailView(APIView):
    def get(self, request, doctor_id=None):
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
    

class DoctorAvailabilityView(APIView):
    def get(self, request):
        """
        Get available time slots for a doctor, excluding booked appointments
        """
        doctor_id = request.query_params.get('doctor_id')
        date = request.query_params.get('date') 

        if not doctor_id:
            return Response(
                {"detail": "Doctor ID is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Get doctor's general availability
            availability = DoctorAvailability.objects.filter(
                doctor_id=doctor_id,
                is_available=True
            )

            # Filter availability by day of week if date is provided
            if date:
                try:
                    # Convert date string to datetime object
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    # Get day name in lowercase
                    day_of_week = date_obj.strftime('%A').lower()
                    # Filter availability for that day
                    availability = availability.filter(day_of_week=day_of_week)
                except ValueError:
                    return Response(
                        {"detail": "Invalid date format. Use YYYY-MM-DD"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Get booked appointments
            appointments = Appointments.objects.filter(
                doctor_id=doctor_id,
                status__in=['scheduled', 'confirmed', 'in_progress']
            )

            if date:
                appointments = appointments.filter(appointment_date=date)
            
            available_slots = []

            for slot in availability:
                # Rest of the code remains the same
                current_time = datetime.combine(
                    datetime.min, 
                    slot.start_time
                )
                end_time = datetime.combine(
                    datetime.min, 
                    slot.end_time
                )
                
                while current_time < end_time:
                    slot_end = current_time + timedelta(minutes=slot.slot_duration)
                    
                    # Check if slot overlaps with any appointment
                    is_available = True
                    for appt in appointments:
                        appt_start = datetime.combine(
                            datetime.min, 
                            appt.start_time
                        )
                        appt_end = datetime.combine(
                            datetime.min, 
                            appt.end_time
                        )
                        
                        if (current_time < appt_end and 
                            slot_end > appt_start and 
                            slot.day_of_week == appt.appointment_date.strftime('%A').lower()):
                            is_available = False
                            break
                    
                    if is_available:
                        available_slots.append({
                            'day_of_week': slot.day_of_week,
                            'start_time': current_time.time().strftime('%H:%M'),
                            'end_time': slot_end.time().strftime('%H:%M'),
                            'duration': slot.slot_duration
                        })
                    
                    current_time = slot_end

            return Response({
                'doctor_id': doctor_id,
                'date': date,
                'day_of_week': day_of_week if date else None,
                'available_slots': available_slots
            })

        except DoctorProfiles.DoesNotExist:
            return Response(
                {"detail": "Doctor not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )