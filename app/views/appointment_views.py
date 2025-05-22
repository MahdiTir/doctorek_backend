from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView

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
        """Get appointments for a specific patient with doctor information."""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({"detail": "Patient ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        appointments = Appointments.objects.filter(patient_id=patient_id).select_related('doctor')
        serializer = self.serializer_class(appointments, many=True, context={'request': request})
        
        # Enhance the response with doctor information
        enhanced_data = []
        for appointment in serializer.data:
            doctor = DoctorProfiles.objects.get(id=appointment['doctor'])
            appointment_data = {
                **appointment,
                'doctor_info': {
                    'full_name': doctor.user.full_name,
                    'speciality': doctor.specialty,
                    'hospital_name': doctor.hospital_name,
                    'avatar_url': doctor.user.avatar_url if doctor.user else None  
                }
            }
            enhanced_data.append(appointment_data)

        return Response(enhanced_data, status=status.HTTP_200_OK)


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
        
class AppointmentsView(APIView):
    def get(self, request):
        """Get list of appointments for the logged in doctor"""
        # Get user id from the token
        doctor_user_id = get_user_id_from_token(request)
        if not doctor_user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            # Get doctor profile
            doctor_profile = DoctorProfiles.objects.get(user_id=doctor_user_id)
            
            # Verify that the user is a doctor
            if doctor_profile.user.user_type != Profiles.UserType.DOCTOR:
                return Response({"detail": "Only doctors can access their appointments"}, 
                               status=status.HTTP_403_FORBIDDEN)
            
            # Get appointments for the doctor
            appointments = Appointments.objects.filter(doctor=doctor_profile).select_related('patient')
            
            # Format the response with required information
            appointments_data = []
            for appointment in appointments:
                appointment_data = {
                    'id': appointment.id,
                    'patient_name': appointment.patient.full_name,
                    'patient_id': appointment.patient.id,
                    'appointment_date': appointment.appointment_date,
                    'start_time': appointment.start_time,
                    'end_time': appointment.end_time,
                    'status': appointment.status,
                    'reason': appointment.reason,
                    'notes': appointment.notes,
                    'created_at': appointment.created_at,
                }
                appointments_data.append(appointment_data)
            
            return Response(appointments_data, status=status.HTTP_200_OK)
            
        except DoctorProfiles.DoesNotExist:
            return Response({"detail": "Doctor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def patch(self, request, appointment_id=None):
        """Update appointment status for a doctor's appointment"""
        # Get user id from the token
        doctor_user_id = get_user_id_from_token(request)
        if not doctor_user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if appointment_id was provided
        if not appointment_id:
            appointment_id = request.data.get('appointment_id')
            if not appointment_id:
                return Response({"detail": "Appointment ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the new status
        new_status = request.data.get('status')
        if not new_status:
            return Response({"detail": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate the status value
        if new_status not in dict(Appointments.Status.choices):
            return Response({"detail": f"Invalid status. Must be one of: {', '.join(dict(Appointments.Status.choices).keys())}"}, 
                         status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get doctor profile
            doctor_profile = DoctorProfiles.objects.get(user_id=doctor_user_id)
            
            # Verify that the user is a doctor
            if doctor_profile.user.user_type != Profiles.UserType.DOCTOR:
                return Response({"detail": "Only doctors can update appointment status"}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            # Get the appointment
            try:
                appointment = Appointments.objects.get(id=appointment_id, doctor=doctor_profile)
            except Appointments.DoesNotExist:
                return Response({"detail": "Appointment not found or you don't have permission to update it"}, 
                              status=status.HTTP_404_NOT_FOUND)
            
            # Update appointment status
            appointment.status = new_status
            
            # Optional: Add notes if provided
            if 'notes' in request.data:
                appointment.notes = request.data.get('notes')
                
            appointment.save()
            
            return Response({
                "detail": "Appointment status updated successfully",
                "appointment_id": appointment.id,
                "new_status": appointment.status
            }, status=status.HTTP_200_OK)
            
        except DoctorProfiles.DoesNotExist:
            return Response({"detail": "Doctor profile not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)