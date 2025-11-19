from django.shortcuts import render
from .forms import TicketForm, RegistrationForm, AddMoneyForm
from .models import Ticket, Station, Line
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
import os
import sys
import fare
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

directory_path = os.path.abspath('F:/code/djangolearn/metro_system/')
sys.path.append(directory_path)

# Create your views here.

def index(request):
    return render(request, 'index.html')

@login_required
def ticket_list(request):
    tickets = Ticket.objects.all()
    return render(request, 'ticket_list.html', {'tickets': tickets})

def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            generated_ticket = fare.metro_system().generate_ticket(ticket.start_station, ticket.end_station)
            if request.user.balance < generated_ticket.price:
                return render(request, 'insufficient_balance.html')
            ticket.price = generated_ticket.price
            ticket.save()
            balance = request.user.balance - ticket.price
            request.user.balance = balance
            request.user.save()
            return redirect('ticket_list')
    else:
        form = TicketForm()

    return render(request, 'ticket_form.html', {'form': form})

@login_required
def ticket_cancel(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    if request.method == 'POST':
        balance = request.user.balance + ticket.price
        ticket.delete()
        request.user.balance = balance
        request.user.save()
        return redirect('ticket_list')
    return render(request, 'ticket_confirm_cancel.html', {'ticket': ticket})

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login(request, user)
            redirect('ticket_list')
    else:
        form = RegistrationForm()
        
    return render(request, 'registration/register.html', {'form':form})

@login_required
def add_money(request):
    if request.method == 'POST':
        form = AddMoneyForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            request.user.balance += amount
            request.user.save()
            return redirect('ticket_list')
    else:
        form = AddMoneyForm()
    
    return render(request, 'add_money.html', {'form': form})

def insufficient_balance(request):
    return render(request, 'insufficient_balance.html')