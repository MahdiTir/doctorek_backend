from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework import status 

from datetime import datetime, time
from ..utils import get_user_id_from_token
import uuid
from django.db import models


import qrcode
import json
import base64
from io import BytesIO


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
        try:
            # Get all appointments with related doctor and patient data
            appointments = Appointments.objects.all().select_related('doctor', 'patient')
            appointments = appointments.order_by('appointment_date', 'start_time')
            
            # Enhanced response with both doctor and patient information
            enhanced_data = []
            for appointment in appointments:
                # Handle cases where doctor or patient is None
                doctor = appointment.doctor
                patient = appointment.patient
                doctor_info = {
                    'id': str(doctor.id) if doctor else None,
                    'full_name': doctor.user.full_name if doctor and doctor.user else None,
                    'specialty': doctor.specialty if doctor else None,
                    'hospital_name': doctor.hospital_name if doctor else None
                } if doctor else None

                patient_info = {
                    'id': str(patient.id) if patient else None,
                    'full_name': patient.full_name if patient else None,
                    'email': patient.email if patient else None
                } if patient else None

                appointment_data = {
                    'id': str(appointment.id),
                    'appointment_date': appointment.appointment_date,
                    'start_time': appointment.start_time,
                    'end_time': appointment.end_time,
                    'status': appointment.status,
                    'reason': appointment.reason,
                    'notes': appointment.notes,
                    'qr_code': appointment.qr_code,
                    'doctor_info': doctor_info,
                    'patient_info': patient_info
                }
                enhanced_data.append(appointment_data)
                
            return Response(enhanced_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'])
    def doctor_appointments(self, request):
        """Get appointments for a specific doctor with filtering options."""
        try:
            doctor_id = request.query_params.get('doctor_id')
            if not doctor_id:
                return Response({"detail": "Doctor ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Get query parameters for filtering
            appointment_status = request.query_params.get('status')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            # Base query with patient information
            appointments = Appointments.objects.filter(doctor_id=doctor_id).select_related('patient')
            
            # Apply filters
            if appointment_status:
                appointments = appointments.filter(status=appointment_status)
            if date_from:
                appointments = appointments.filter(appointment_date__gte=date_from)
            if date_to:
                appointments = appointments.filter(appointment_date__lte=date_to)
                
            appointments = appointments.order_by('appointment_date', 'start_time')
            
            # Enhanced response with patient information
            appointments_data = []
            for appointment in appointments:
                appointment_data = {
                    'id': str(appointment.id),
                    'appointment_date': appointment.appointment_date,
                    'start_time': appointment.start_time,
                    'end_time': appointment.end_time,
                    'status': appointment.status,
                    'reason': appointment.reason,
                    'notes': appointment.notes,
                    'patient_info': {
                        'id': str(appointment.patient.id),
                        'full_name': appointment.patient.full_name,
                        'email': appointment.patient.email,
                        'phone_number': appointment.patient.phone_number
                    }
                }
                appointments_data.append(appointment_data)
            
            return Response(appointments_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def patient_appointments(self, request):
        """Get appointments for a specific patient with doctor information."""
        try:
            patient_id = request.query_params.get('patient_id')
            if not patient_id:
                return Response({"detail": "Patient ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Get query parameters for filtering
            appointment_status = request.query_params.get('status')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            # Base query with doctor information
            appointments = Appointments.objects.filter(
                patient_id=patient_id
            ).select_related('doctor', 'doctor__user')
            
            # Apply filters
            if appointment_status:
                appointments = appointments.filter(status=appointment_status)
            if date_from:
                appointments = appointments.filter(appointment_date__gte=date_from)
            if date_to:
                appointments = appointments.filter(appointment_date__lte=date_to)
                
            appointments = appointments.order_by('appointment_date', 'start_time')
            
            # Enhanced response with doctor information
            appointments_data = []
            for appointment in appointments:
                appointment_data = {
                    'id': str(appointment.id),
                    'appointment_date': appointment.appointment_date,
                    'start_time': appointment.start_time,
                    'end_time': appointment.end_time,
                    'status': appointment.status,
                    'reason': appointment.reason,
                    'notes': appointment.notes,
                    'qr_code': appointment.qr_code,
                    'doctor_info': {
                        'id': str(appointment.doctor.id),
                        'full_name': appointment.doctor.user.full_name,
                        'specialty': appointment.doctor.specialty,
                        'hospital_name': appointment.doctor.hospital_name,
                        'avatar_url': appointment.doctor.user.avatar_url
                    }
                }
                appointments_data.append(appointment_data)
            
            return Response(appointments_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """Cancel an existing appointment with validation and notification."""
        try:
            appointment = self.get_object()
            
            # Validate if appointment can be cancelled
            if appointment.status == Appointments.Status.CANCELLED:
                return Response(
                    {"detail": "Appointment is already cancelled"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if appointment.status == Appointments.Status.COMPLETED:
                return Response(
                    {"detail": "Cannot cancel a completed appointment"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Check if appointment is in the past
            if appointment.appointment_date < datetime.now().date():
                return Response(
                    {"detail": "Cannot cancel past appointments"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Update appointment status
            appointment.status = Appointments.Status.CANCELLED
            
            # Add cancellation reason if provided
            if 'reason' in request.data:
                appointment.notes = f"Cancellation reason: {request.data['reason']}"
                
            appointment.save()
            
            # Return success response with updated appointment data
            serializer = self.serializer_class(appointment)
            return Response({
                "detail": "Appointment cancelled successfully",
                "appointment": serializer.data
            }, status=status.HTTP_200_OK)

        except Appointments.DoesNotExist:
            return Response(
                {"detail": "Appointment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
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
                return Response({"detail": "Only patients can create appointments"}, 
                            status=status.HTTP_403_FORBIDDEN)

            # Get the doctor profile
            doctor_id = request.data.get('doctor_id')
            doctor = DoctorProfiles.objects.get(id=doctor_id)
            
            # Validate appointment time
            start_time = request.data.get('start_time')
            end_time = request.data.get('end_time')
            appointment_date = request.data.get('appointment_date')
            
            # Convert times to datetime.time objects for comparison
            appt_start = datetime.strptime(start_time, '%H:%M:%S').time()
            appt_end = datetime.strptime(end_time, '%H:%M:%S').time()
            appt_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()

            # Validate appointment is not in the past
            if appt_date < datetime.now().date():
                return Response({
                    "detail": "Cannot create appointments for past dates"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if doctor is available at this time
            availability = DoctorAvailability.objects.filter(
                doctor_id=doctor_id,
                day_of_week=datetime.strptime(appointment_date, '%Y-%m-%d').strftime('%A').lower(),
                is_available=True
            ).first()
            
            if not availability:
                return Response({
                    "detail": "Doctor is not available on this day"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if appointment time is within availability time
            if appt_start < availability.start_time or appt_end > availability.end_time:
                return Response({
                    "detail": "Appointment time must be within doctor's availability hours"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check for overlapping appointments
            overlapping_appointments = Appointments.objects.filter(
                doctor_id=doctor_id,
                appointment_date=appointment_date
            ).exclude(status=Appointments.Status.CANCELLED)
            
            # Check each existing appointment for overlap
            for existing_appt in overlapping_appointments:
                if (
                    (appt_start >= existing_appt.start_time and appt_start < existing_appt.end_time) or  # Start time overlaps
                    (appt_end > existing_appt.start_time and appt_end <= existing_appt.end_time) or      # End time overlaps
                    (appt_start <= existing_appt.start_time and appt_end >= existing_appt.end_time)      # Appointment encompasses existing
                ):
                    return Response({
                        "detail": "This time slot conflicts with an existing appointment"
                    }, status=status.HTTP_400_BAD_REQUEST)

            appointment_id = uuid.uuid4()
            
            # Create QR code data
            qr_data = {
                'appointment_id': str(appointment_id),
                'patient': {
                    'id': str(patient.id),
                    'name': patient.full_name,
                    'email': patient.email
                },
                'doctor': {
                    'id': str(doctor.id),
                    'name': doctor.user.full_name,
                    'specialty': doctor.specialty,
                    'hospital': doctor.hospital_name
                },
                'appointment': {
                    'date': appointment_date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'status': Appointments.Status.SCHEDULED
                }
            }
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            # Create QR code image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert QR code to base64 string
            buffered = BytesIO()
            qr_image.save(buffered, format="PNG")
            qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Create appointment data
            appointment_data = {
                'id': appointment_id,
                'patient': patient.id,
                'doctor': doctor.id,
                'appointment_date': appointment_date,
                'start_time': start_time,
                'end_time': end_time,
                'status': Appointments.Status.SCHEDULED,
                'reason': request.data.get('reason'),
                'notes': request.data.get('notes'),
                'qr_code': f"data:image/png;base64,{qr_code_base64}"
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

            # Validate required fields
            if not all([new_start_time, new_end_time, new_date]):
                return Response({
                    "detail": "start_time, end_time, and appointment_date are required"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate that appointment is not in the past
            if datetime.strptime(new_date, '%Y-%m-%d').date() < datetime.now().date():
                return Response({
                    "detail": "Cannot reschedule to a past date"
                }, status=status.HTTP_400_BAD_REQUEST)

            # ... existing availability and conflict checks ...

            # Update appointment details
            appointment.start_time = new_start_time
            appointment.end_time = new_end_time
            appointment.appointment_date = new_date
            appointment.save()

            # Generate new QR code for rescheduled appointment
            qr_data = {
                'appointment_id': str(appointment.id),
                'patient': {
                    'id': str(appointment.patient.id),
                    'name': appointment.patient.full_name,
                    'email': appointment.patient.email
                },
                'doctor': {
                    'id': str(appointment.doctor.id),
                    'name': appointment.doctor.user.full_name,
                    'specialty': appointment.doctor.specialty,
                    'hospital': appointment.doctor.hospital_name
                },
                'appointment': {
                    'date': new_date,
                    'start_time': new_start_time,
                    'end_time': new_end_time,
                    'status': appointment.status
                }
            }
            
            # Generate new QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            qr_image.save(buffered, format="PNG")
            qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Update QR code
            appointment.qr_code = f"data:image/png;base64,{qr_code_base64}"
            appointment.save()

            return Response({
                "detail": "Appointment rescheduled successfully",
                "appointment": self.serializer_class(appointment).data
            }, status=status.HTTP_200_OK)

        except Appointments.DoesNotExist:
            return Response({"detail": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'])
    def modify_status(self, request, pk=None):
        """Modify appointment status and update QR code."""
        try:
            appointment = self.get_object()
            new_status = request.data.get('status')

            # Validate status
            if not new_status:
                return Response({
                    "detail": "Status is required"
                }, status=status.HTTP_400_BAD_REQUEST)

            if new_status not in dict(Appointments.Status.choices):
                return Response({
                    "detail": f"Invalid status. Must be one of: {', '.join(dict(Appointments.Status.choices).keys())}"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update appointment status
            appointment.status = new_status

            # Generate new QR code with updated status
            qr_data = {
                'appointment_id': str(appointment.id),
                'patient': {
                    'id': str(appointment.patient.id),
                    'name': appointment.patient.full_name,
                    'email': appointment.patient.email
                },
                'doctor': {
                    'id': str(appointment.doctor.id),
                    'name': appointment.doctor.user.full_name,
                    'specialty': appointment.doctor.specialty,
                    'hospital': appointment.doctor.hospital_name
                },
                'appointment': {
                    'date': str(appointment.appointment_date),
                    'start_time': str(appointment.start_time),
                    'end_time': str(appointment.end_time),
                    'status': new_status
                }
            }

            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(qr_data))
            qr.make(fit=True)

            # Generate QR image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            qr_image.save(buffered, format="PNG")
            qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Update appointment QR code
            appointment.qr_code = f"data:image/png;base64,{qr_code_base64}"
            
            # Add status change note if provided
            if 'notes' in request.data:
                appointment.notes = f"Status changed to {new_status}: {request.data['notes']}"
            
            appointment.save()

            return Response({
                "detail": "Appointment status updated successfully",
                "appointment": self.serializer_class(appointment).data
            }, status=status.HTTP_200_OK)

        except Appointments.DoesNotExist:
            return Response(
                {"detail": "Appointment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        

    