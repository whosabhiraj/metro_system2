from django.contrib import admin
from .models import Ticket, Station, Line
# Register your models here.

admin.site.register(Ticket)
admin.site.register(Station)
admin.site.register(Line)
