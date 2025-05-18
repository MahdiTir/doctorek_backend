from rest_framework import viewsets, status
from rest_framework.response import Response
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
    


    def create(self, request, *args, **kwargs):
        # Get authenticated user
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        # Validate required fields
        required_fields = ['doctor_id', 'appointment_date', 'start_time', 'end_time']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {"detail": f"{field} is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Convert times to time objects for comparison
        try:
            start_time = datetime.strptime(request.data['start_time'], '%H:%M').time()
            end_time = datetime.strptime(request.data['end_time'], '%H:%M').time()
            appointment_date = datetime.strptime(request.data['appointment_date'], '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid time or date format"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate time order
        if start_time >= end_time:
            return Response(
                {"detail": "Start time must be before end time"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check doctor availability
        doctor_id = request.data['doctor_id']
        try:
            day_of_week = appointment_date.strftime('%A').lower()
            availability = DoctorAvailability.objects.filter(
                doctor_id=doctor_id,
                day_of_week=day_of_week,
                is_available=True
            ).first()

            if not availability:
                return Response(
                    {"detail": "Doctor is not available on this day"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if appointment time is within doctor's available hours
            if start_time < availability.start_time or end_time > availability.end_time:
                return Response(
                    {"detail": "Appointment time is outside doctor's available hours"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check for overlapping appointments
            overlapping_appointments = Appointments.objects.filter(
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                status__in=['scheduled', 'confirmed', 'in_progress'],
            ).exclude(
                start_time__gte=end_time
            ).exclude(
                end_time__lte=start_time
            )

            if overlapping_appointments.exists():
                return Response(
                    {"detail": "This time slot is already booked"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        except DoctorAvailability.DoesNotExist:
            return Response(
                {"detail": "Doctor's availability not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Prepare appointment data
        appointment_data = {
            'id': uuid.uuid4(),
            'patient_id': user_id,
            'doctor_id': doctor_id,
            'appointment_date': appointment_date,
            'start_time': start_time,
            'end_time': end_time,
            'status': Appointments.Status.SCHEDULED,
            'reason': request.data.get('reason'),
            'notes': request.data.get('notes'),
        }

        # Create appointment
        serializer = self.get_serializer(data=appointment_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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