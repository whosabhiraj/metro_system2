from ticket.models import Ticket
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

def mark():
    old = timezone.now() - timedelta(days = 1)
    Ticket.objects.filter(status = 'ACTIVE', created_at__lt = old).update(status='EXPIRED')
    Ticket.objects.filter(status = 'IN_USE', created_at__lt = old).update(status='USED')

mark()
print("marked") # debug
