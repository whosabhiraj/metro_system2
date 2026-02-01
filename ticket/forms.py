from django import forms
from .models import Ticket, Station, Line, CustomUser
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class TicketForm(forms.ModelForm):
    start_station = forms.ModelChoiceField(
        queryset=Station.objects.all().order_by("id"),
        label="Start Station",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    end_station = forms.ModelChoiceField(
        queryset=Station.objects.all().order_by("id"),
        label="End Station",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    otp = forms.IntegerField(required=False)

    class Meta:
        model = Ticket
        fields = ["start_station", "end_station"]


class RegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            "username",
            "email",
            "balance",
            "password1",
            "password2",
            "first_name",
            "last_name",
        ]

    username = forms.CharField(max_length=30)
    email = forms.EmailField()
    balance = forms.IntegerField(initial=0, max_value=9999999)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)


class AddMoneyForm(forms.Form):
    amount = forms.IntegerField(label="Amount to Add", min_value=0, max_value=9999999)
