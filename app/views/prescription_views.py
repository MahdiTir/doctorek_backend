from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from datetime import datetime
import uuid

from ..models import (
    Prescriptions,
    Profiles,
    DoctorProfiles,
    Appointments
)
from ..serializers import PrescriptionSerializer
from ..utils import get_user_id_from_token

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescriptions.objects.all()
    serializer_class = PrescriptionSerializer

    def get_queryset(self):
        """Filter prescriptions based on query parameters"""
        queryset = Prescriptions.objects.all()
        patient_id = self.request.query_params.get('patient', None)
        doctor_id = self.request.query_params.get('doctor', None)
        appointment_id = self.request.query_params.get('appointment', None)

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if appointment_id:
            queryset = queryset.filter(appointment_id=appointment_id)

        return queryset

    def create(self, request):
        """Create a new prescription"""
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Get the doctor profile
            doctor = DoctorProfiles.objects.get(user_id=user_id)

            if doctor.user.user_type != Profiles.UserType.DOCTOR:
                return Response({"detail": "Only doctors can create prescriptions"}, 
                              status=status.HTTP_403_FORBIDDEN)
            

            # Get appointment if provided
            appointment_id = request.data.get('appointment_id')
            patient_id = request.data.get('patient_id')

            # Check if appointment already has a prescription
            existing_prescription = Prescriptions.objects.filter(appointment_id=appointment_id).first()
            if existing_prescription:
                return Response(
                    {"detail": "This appointment already has a prescription"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            appointment = Appointments.objects.get(id=appointment_id)

             # Verify that the doctor creating the prescription is the same as in appointment
            if str(appointment.doctor.id) != str(doctor.id):
                return Response({"detail": "You can only create prescriptions for your own appointments"}, 
                            status=status.HTTP_403_FORBIDDEN)
            
            # Verify that the patient in the request matches the appointment
            if str(appointment.patient.id) != str(patient_id):
                return Response({"detail": "Patient ID does not match the appointment"}, 
                            status=status.HTTP_400_BAD_REQUEST)

            if appointment is None:
                return Response({"detail": "appointment id not valid"}, 
                              status=status.HTTP_403_FORBIDDEN)
            

            # Create prescription data
            prescription_data = {
                'id': uuid.uuid4(),
                'patient': request.data.get('patient_id'),
                'doctor': doctor.id,
                'appointment': appointment.id if appointment else None,
                'prescription_date': datetime.now().date(),
                'details': request.data.get('details', {}),
                'additional_notes': request.data.get('additional_notes'),
                'pdf_url': request.data.get('pdf_url'),
                'is_synced': False,
                #'created_at': datetime.now(),
                #'updated_at': datetime.now(),
                'local_id': request.data.get('local_id')
            }

            serializer = self.serializer_class(data=prescription_data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except DoctorProfiles.DoesNotExist:
            return Response({"detail": "Doctor profile not found"}, 
                          status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        """Update an existing prescription"""
        try:
            prescription = self.get_object()
            user_id = get_user_id_from_token(request)

            # Verify ownership
            if str(prescription.doctor.user.id) != str(user_id):
                return Response({"detail": "Not authorized to update this prescription"}, 
                              status=status.HTTP_403_FORBIDDEN)

            # Update fields
            for key, value in request.data.items():
                if hasattr(prescription, key):
                    setattr(prescription, key, value)
            prescription.updated_at = datetime.now()
            prescription.save()

            serializer = self.serializer_class(prescription)
            return Response(serializer.data)

        except Exception as e:
            return Response({"detail": str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        """Delete a prescription"""
        try:
            prescription = self.get_object()
            user_id = get_user_id_from_token(request)

            # Verify ownership
            if str(prescription.doctor.user.id) != str(user_id):
                return Response({"detail": "Not authorized to delete this prescription"}, 
                              status=status.HTTP_403_FORBIDDEN)

            prescription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return Response({"detail": str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def patient_prescriptions(self, request):
        """Get prescriptions for a specific patient"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({"detail": "Patient ID is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        prescriptions = self.get_queryset().filter(patient_id=patient_id)
        serializer = self.serializer_class(prescriptions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def doctor_prescriptions(self, request):
        """Get prescriptions created by a specific doctor"""
        doctor_id = request.query_params.get('doctor_id')
        if not doctor_id:
            return Response({"detail": "Doctor ID is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)

        prescriptions = self.get_queryset().filter(doctor_id=doctor_id)
        serializer = self.serializer_class(prescriptions, many=True)
        return Response(serializer.data)