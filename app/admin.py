from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Appointments)
admin.site.register(Prescriptions)
admin.site.register(Profiles)
admin.site.register(DoctorProfiles)
admin.site.register(DoctorAvailability)
admin.site.register(FavoriteDoctors)
admin.site.register(Notifications)
