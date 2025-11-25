from django.contrib import admin
from .models import Ticket, Station, Line, ScannerProfile, ThroughTable
# Register your models here.

admin.site.register(Ticket)
admin.site.register(Station)
admin.site.register(Line)
admin.site.register(ScannerProfile)
admin.site.register(ThroughTable)
