from django import forms
from .models import Ticket, Station, Line, CustomUser
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['start_station', 'end_station']
        
class RegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'balance', 'password1', 'password2', 'first_name', 'last_name']
    username = forms.CharField(max_length=30)
    email = forms.EmailField()
    balance = forms.IntegerField(initial=0)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

class AddMoneyForm(forms.Form):
    amount = forms.IntegerField(label="Amount to Add")
