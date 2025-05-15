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
    patient = ProfileSerializer(read_only=True)
    doctor = DoctorProfileSerializer(read_only=True)

    class Meta:
        model = Appointments
        fields = '__all__'

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

