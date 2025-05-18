# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'






class Notifications(models.Model):
    class Types(models.TextChoices):
        APPOINTMENT_REMINDER = 'appointment_reminder', 'Appointment Reminder'
        APPOINTMENT_CONFIRMATION = 'appointment_confirmation', 'Appointment Confirmation'
        APPOINTMENT_CANCELLED = 'appointment_cancelled', 'Appointment Cancelled'
        PRESCRIPTION_READY = 'prescription_ready', 'Prescription Ready'
        DOCTOR_MESSAGE = 'doctor_message', 'Doctor Message'
        SYSTEM_MESSAGE = 'system_message', 'System Message'
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey('Profiles', models.DO_NOTHING)
    type = models.CharField(
        max_length=30,
        choices=Types.choices,
        default=Types.SYSTEM_MESSAGE,
    )
    title = models.TextField()
    content = models.TextField()
    is_read = models.BooleanField()
    related_id = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'notifications'




class Profiles(models.Model):
    class UserType(models.TextChoices):
        PATIENT = 'patient', 'Patient'
        DOCTOR = 'doctor', 'Doctor'
    id = models.UUIDField(primary_key=True)  
    #id = models.UUIDField(primary_key=True, editable=False)
    email = models.TextField(blank=True, null=True)
    phone_number = models.TextField(blank=True, null=True)
    full_name = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    avatar_url = models.TextField(blank=True, null=True)
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.PATIENT
    )
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'profiles'


class DoctorProfiles(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(Profiles, models.CASCADE, related_name='doctor_profiles', db_column='user_id')
    specialty = models.TextField()
    hospital_name = models.TextField(blank=True, null=True)
    hospital_address = models.TextField(blank=True, null=True)
    location_lat = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    location_lng = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    years_of_experience = models.IntegerField(blank=True, null=True)
    contact_information = models.JSONField(blank=True, null=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'doctor_profiles'



class FavoriteDoctors(models.Model):
    id = models.UUIDField(primary_key=True)
    patient = models.ForeignKey(Profiles, models.CASCADE, related_name='favorite_doctors')
    doctor = models.ForeignKey(DoctorProfiles, models.CASCADE, related_name='favorite_doctors')
    created_at = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'favorite_doctors'
        unique_together = (('patient', 'doctor'),)

class Appointments(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        CONFIRMED = 'confirmed', 'Confirmed'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No Show'

    id = models.UUIDField(primary_key=True)
    patient = models.ForeignKey(Profiles, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfiles, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    qr_code = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)     
    last_sync = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'appointments'
        managed = False  

class DoctorAvailability(models.Model):
    class DaysOfWeek(models.TextChoices):
        MONDAY = 'monday', 'Monday'
        TUESDAY = 'tuesday', 'Tuesday'
        WEDNESDAY = 'wednesday', 'Wednesday'
        THURSDAY = 'thursday', 'Thursday'
        FRIDAY = 'friday', 'Friday'
        SATURDAY = 'saturday', 'Saturday'
        SUNDAY = 'sunday', 'Sunday'
    
    id = models.UUIDField(primary_key=True)
    doctor = models.ForeignKey(DoctorProfiles, models.CASCADE, related_name='availability')
    day_of_week = models.CharField(
        max_length=10,   
        choices=DaysOfWeek.choices,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.IntegerField()
    is_available = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'doctor_availability'
        unique_together = (('doctor', 'day_of_week', 'start_time'),)

class Prescriptions(models.Model):
    id = models.UUIDField(primary_key=True)
    appointment = models.ForeignKey(Appointments, models.CASCADE, related_name="prescriptions", blank=True, null=True)
    patient = models.ForeignKey(Profiles, models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(DoctorProfiles, models.CASCADE, related_name='prescriptions')
    prescription_date = models.DateField()
    details = models.JSONField()
    additional_notes = models.TextField(blank=True, null=True)
    pdf_url = models.TextField(blank=True, null=True)
    is_synced = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    local_id = models.TextField(unique=True, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'prescriptions'