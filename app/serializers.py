from rest_framework import serializers
from .models import (
    Profiles, 
    DoctorProfiles, 
    DoctorAvailability,
    Appointments,
    Prescriptions,
    FavoriteDoctors,
    Notifications
)

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profiles
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class DoctorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorAvailability
        fields = '__all__'

class DoctorProfileSerializer(serializers.ModelSerializer):
    availability = DoctorAvailabilitySerializer(many=True, read_only=True)
    user = ProfileSerializer(read_only=True)

    class Meta:
        model = DoctorProfiles
        fields = '__all__'
    
    def create(self, validated_data):
        return DoctorProfiles.objects.create(**validated_data)

class AppointmentSerializer(serializers.ModelSerializer):
    patient_id = serializers.UUIDField(source='patient.id',read_only=True)
    doctor_id = serializers.UUIDField(source='doctor.id',read_only=True)

    class Meta:
        model = Appointments
        #fields = '__all__'
        fields = [
                 'id',
                 'patient', 'doctor', 'patient_id', 'doctor_id', 
                 'appointment_date', 'start_time', 'end_time', 'status', 
                 'reason', 'notes', 'qr_code', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class PrescriptionSerializer(serializers.ModelSerializer):
    patient = ProfileSerializer(read_only=True)
    doctor = DoctorProfileSerializer(read_only=True)
    appointment = AppointmentSerializer(read_only=True)

    class Meta:
        model = Prescriptions
        fields = '__all__'

class FavoriteDoctorSerializer(serializers.ModelSerializer):
    patient = ProfileSerializer(read_only=True)
    doctor = DoctorProfileSerializer(read_only=True)

    class Meta:
        model = FavoriteDoctors
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    user = ProfileSerializer(read_only=True)

    class Meta:
        model = Notifications
        fields = '__all__'

class DoctorDetailSerializer(serializers.ModelSerializer):
    # Nested profile information
    profiles = serializers.SerializerMethodField()
    # Nested availability information
    doctor_availability = serializers.SerializerMethodField()
    
    class Meta:
        model = DoctorProfiles
        fields = [
            'id', 'user_id', 'specialty', 'hospital_name', 'hospital_address',
            'location_lat', 'location_lng', 'bio', 'years_of_experience',
            'contact_information', 'average_rating', 'created_at', 'updated_at',
            'profiles', 'doctor_availability'
        ]
    
    def get_profiles(self, obj):
        """Get profile information from related user"""
        if not obj.user:
            return None
        return {
            'full_name': obj.user.full_name,
            'avatar_url': obj.user.avatar_url
        }
    
    def get_doctor_availability(self, obj):
        """Get availability days that are marked as available"""
        availabilities = DoctorAvailability.objects.filter(
            doctor_id=obj.id,
            is_available=True
        ).values('day_of_week', 'is_available')
        
        return list(availabilities)