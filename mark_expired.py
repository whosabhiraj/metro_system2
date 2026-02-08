from ticket.models import Ticket, OTP
from django.utils import timezone
from datetime import timedelta

def mark():
    Ticket.objects.filter(status = 'ACTIVE', created_at__lt = timezone.now()).update(status='EXPIRED')
    Ticket.objects.filter(status = 'IN_USE', created_at__lt = timezone.now()).update(status='USED')
    OTP.objects.filter(created_at__lt = timezone.now() - timedelta(minutes=15)).delete()

mark()
print("marked") # debug
