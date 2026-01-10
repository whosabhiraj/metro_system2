from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Ticket)
admin.site.register(Station)
admin.site.register(Line)
admin.site.register(ScannerProfile)
admin.site.register(ThroughTable)
admin.site.register(OTP)
admin.site.register(ServiceStatus)
admin.site.register(CustomUser)
