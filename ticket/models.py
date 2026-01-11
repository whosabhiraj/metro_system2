from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.conf import settings

# Create your models here.


class Station(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Line(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)  # thruogh tsble
    stations = models.ManyToManyField(
        Station,
        through="ThroughTable",
        through_fields=("line", "station"),
        related_name="lines",
    )

    def __str__(self):
        return self.name


class ThroughTable(models.Model):
    line = models.ForeignKey(Line, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        unique_together = ("line", "order")

    def __str__(self):
        return f"Station: {self.station.name} on Line: {self.line.name} at position {self.order}"


class CustomUser(AbstractUser):
    balance = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.username


class Ticket(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_station = models.ForeignKey(
        Station, related_name="start", on_delete=models.CASCADE
    )
    end_station = models.ForeignKey(
        Station, related_name="end", on_delete=models.CASCADE
    )

    price = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    uid = models.CharField(max_length=20)
    scan_in = models.DateTimeField(null=True)
    scan_out = models.DateTimeField(null=True)

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        IN_USE = "IN_USE", "In Use"
        EXPIRED = "EXPIRED", "Expired"
        USED = "USED", "Used"
        CANCELLED = "CANCELLED", "Cancelled"

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE
    )

    def __str__(self):
        return f"Ticket for {self.user.username}"


class ScannerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)  # foreign key

    def __str__(self):
        return f"{self.user.username} - {self.station}"


class OTP(models.Model):
    code = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class ServiceStatus(models.Model):
    active = models.BooleanField(default=True)
