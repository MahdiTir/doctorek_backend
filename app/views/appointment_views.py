from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from datetime import datetime, time
from ..utils import get_user_id_from_token
import uuid
from django.db import models

from ..models import (
    Appointments,
    Prescriptions,
    DoctorAvailability,
    Profiles,
    DoctorProfiles
)
from ..serializers import (
    AppointmentSerializer,
    PrescriptionSerializer,
)

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
    

    @action(detail=False, methods=['get'])
    def all_appointments(self, request):
        """Get all appointments."""
        appointments = Appointments.objects.all()
        serializer = self.serializer_class(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def doctor_appointments(self, request):
        """Get appointments for a specific doctor."""
        doctor_id = request.query_params.get('doctor_id')
        if not doctor_id:
            return Response({"detail": "Doctor ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        appointments = Appointments.objects.filter(doctor_id=doctor_id)
        serializer = self.serializer_class(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def patient_appointments(self, request):
        """Get appointments for a specific patient."""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({"detail": "Patient ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        appointments = Appointments.objects.filter(patient_id=patient_id)
        serializer = self.serializer_class(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def create(self, request):
        """Create a new appointment"""
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Get the patient profile
            patient = Profiles.objects.get(id=user_id)
            
            # Verify that the user is a patient
            if patient.user_type != Profiles.UserType.PATIENT:
                return Response({"detail": "Only patients can create appointments"}, status=status.HTTP_403_FORBIDDEN)

            # Get the doctor profile
            doctor_id = request.data.get('doctor_id')
            doctor = DoctorProfiles.objects.get(id=doctor_id)
            
            # Validate appointment time
            start_time = request.data.get('start_time')
            end_time = request.data.get('end_time')
            appointment_date = request.data.get('appointment_date')
            
            # Check if doctor is available at this time
            availability = DoctorAvailability.objects.filter(
                doctor_id=doctor_id,
                day_of_week=datetime.strptime(appointment_date, '%Y-%m-%d').strftime('%A').lower(),
                start_time__lte=start_time,
                end_time__gte=end_time,
                is_available=True
            ).first()
            
            if not availability:
                return Response({
                    "detail": "Doctor is not available at this time"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check for existing appointments at the same time
            existing_appointment = Appointments.objects.filter(
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(status=Appointments.Status.CANCELLED).exists()
            
            if existing_appointment:
                return Response({
                    "detail": "This time slot is already booked"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create appointment data
            appointment_data = {
                'id': uuid.uuid4(), 
                'patient': patient.id,
                'doctor': doctor.id,
                'appointment_date': appointment_date,
                'start_time': start_time,
                'end_time': end_time,
                'status': Appointments.Status.SCHEDULED,
                'reason': request.data.get('reason'),
                'notes': request.data.get('notes'),
            }
            
            # Create the appointment
            serializer = self.serializer_class(data=appointment_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Profiles.DoesNotExist:
            return Response({"detail": "Patient profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except DoctorProfiles.DoesNotExist:
            return Response({"detail": "Doctor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

  
    @action(detail=True, methods=['patch'])
    def reschedule(self, request, pk=None):
        """Reschedule an existing appointment"""
        try:
            appointment = self.get_object()
            new_start_time = request.data.get('start_time')
            new_end_time = request.data.get('end_time')
            new_date = request.data.get('appointment_date')

            # Validate new appointment time
            availability = DoctorAvailability.objects.filter(
                doctor_id=appointment.doctor.id,
                day_of_week=datetime.strptime(new_date, '%Y-%m-%d').strftime('%A').lower(),
                start_time__lte=new_start_time,
                end_time__gte=new_end_time,
                is_available=True
            ).first()

            if not availability:
                return Response({
                    "detail": "Doctor is not available at this time"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check for conflicting appointments
            conflicting_appointment = Appointments.objects.filter(
                doctor_id=appointment.doctor.id,
                appointment_date=new_date,
                start_time__lt=new_end_time,
                end_time__gt=new_start_time
            ).exclude(id=appointment.id).exists()

            if conflicting_appointment:
                return Response({
                    "detail": "This time slot is already booked"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update appointment details
            appointment.start_time = new_start_time
            appointment.end_time = new_end_time
            appointment.appointment_date = new_date
            appointment.save()

            return Response({
                "detail": "Appointment rescheduled successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """Cancel an existing appointment"""
        try:
            appointment = self.get_object()
            appointment.status = Appointments.Status.CANCELLED
            appointment.save()

            return Response({
                "detail": "Appointment canceled successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)