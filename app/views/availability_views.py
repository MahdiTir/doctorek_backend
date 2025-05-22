from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from datetime import datetime, timedelta
import uuid 

from ..models import (
    DoctorAvailability,
    DoctorProfiles,
    Appointments
)
from ..serializers import DoctorAvailabilitySerializer
from ..utils import get_user_id_from_token

class DoctorAvailabilityManagementView(APIView):
    """View for managing doctor availability"""
    
    def get(self, request):
        """Get availability for the logged-in doctor"""
        doctor_user_id = get_user_id_from_token(request)
        if not doctor_user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        try:
            doctor_profile = DoctorProfiles.objects.get(user_id=doctor_user_id)
            availability = DoctorAvailability.objects.filter(doctor=doctor_profile)
            
            availability_data = []
            for slot in availability:
                slot_data = {
                    'id': slot.id,
                    'day_of_week': slot.day_of_week,
                    'start_time': slot.start_time,
                    'end_time': slot.end_time,
                    'slot_duration': slot.slot_duration,
                    'is_available': slot.is_available
                }
                availability_data.append(slot_data)
                
            return Response(availability_data, status=status.HTTP_200_OK)
            
        except DoctorProfiles.DoesNotExist:
            return Response({"detail": "Doctor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Create new availability slot for the logged-in doctor"""
        doctor_user_id = get_user_id_from_token(request)
        if not doctor_user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            doctor_profile = DoctorProfiles.objects.get(user_id=doctor_user_id)
            
            # Add doctor_id to the request data
            availability_data = request.data.copy()
            availability_data['doctor'] = doctor_profile.id
            availability_data['id'] = uuid.uuid4() 
            availability_data['created_at'] = datetime.now()
            availability_data['updated_at'] = datetime.now()
            
            serializer = DoctorAvailabilitySerializer(data=availability_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except DoctorProfiles.DoesNotExist:
            return Response({"detail": "Doctor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, availability_id):
        """Update an existing availability slot"""
        doctor_user_id = get_user_id_from_token(request)
        if not doctor_user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            doctor_profile = DoctorProfiles.objects.get(user_id=doctor_user_id)
            availability = DoctorAvailability.objects.get(
                id=availability_id,
                doctor=doctor_profile
            )
            
            # Update the availability data
            availability_data = request.data.copy()
            availability_data['doctor'] = doctor_profile.id
            availability_data['updated_at'] = datetime.now()
            
            serializer = DoctorAvailabilitySerializer(availability, data=availability_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except DoctorAvailability.DoesNotExist:
            return Response({"detail": "Availability slot not found"}, status=status.HTTP_404_NOT_FOUND)
        except DoctorProfiles.DoesNotExist:
            return Response({"detail": "Doctor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, availability_id):
        """Delete an availability slot"""
        doctor_user_id = get_user_id_from_token(request)
        if not doctor_user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            doctor_profile = DoctorProfiles.objects.get(user_id=doctor_user_id)
            availability = DoctorAvailability.objects.get(
                id=availability_id,
                doctor=doctor_profile
            )
            
            availability.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except DoctorAvailability.DoesNotExist:
            return Response({"detail": "Availability slot not found"}, status=status.HTTP_404_NOT_FOUND)
        except DoctorProfiles.DoesNotExist:
            return Response({"detail": "Doctor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)