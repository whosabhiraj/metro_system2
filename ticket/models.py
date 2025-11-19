from django.db import models
from django.contrib.auth.models import User, AbstractUser
import uuid
from django.conf import settings 

# Create your models here.

class Ticket(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_station = models.CharField(max_length=100)
    end_station = models.CharField(max_length=100)
    price = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket for {self.user.username}"
    
class Station(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    line = models.ForeignKey('Line', on_delete=models.CASCADE, related_name='stations')

    def __str__(self):
        return self.name
    
class Line(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class CustomUser(AbstractUser):
    balance = models.IntegerField(default=0)

    def __str__(self):
        return self.username
    