from django.shortcuts import render
from .forms import TicketForm, RegistrationForm, AddMoneyForm
from .models import Ticket, Station, Line, ScannerProfile
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.models import User
import os
import sys
import metro_orm as fare
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages

directory_path = os.path.abspath('F:/code/djangolearn/metro_system/')
sys.path.append(directory_path)

# Create your views here.

def index(request):
    return render(request, 'index.html')

@login_required
def ticket_list(request):
    # if ScannerProfile:
    #     return redirect("scanner")
    # else:
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
            balance = request.user.balance - ticket.price
            request.user.balance = balance
            request.user.save()
            uid = generated_ticket.id

            Ticket.objects.create(
            user = request.user,
            uid=uid,
            start_station=ticket.start_station,
            end_station=ticket.end_station,
            price=ticket.price
        )
            
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

@login_required
def scan_ticket(request):
    try:
        scanner_location = request.user.scannerprofile.station
    except ScannerProfile.DoesNotExist: 
        messages.error(request, "Access Denied: No station assigned.")
        return redirect('index')

    if request.method == 'POST':
        uid = request.POST.get('ticket_uid').strip()
        
        try:
            ticket = Ticket.objects.get(uid=uid)
            
            if ticket.status == Ticket.Status.ACTIVE:
                if ticket.start_station.lower() == scanner_location.lower():
                    ticket.status = Ticket.Status.IN_USE
                    ticket.save()
                    messages.success(request, f"Entry Approved at {scanner_location}!")
                else:
                    messages.error(request, f"Wrong Station. Ticket is for {ticket.start_station}.")

            elif ticket.status == Ticket.Status.IN_USE:
                if ticket.end_station.lower() == scanner_location.lower():
                    ticket.status = Ticket.Status.EXPIRED
                    ticket.save()
                    messages.success(request, f"Exit Approved at {scanner_location}!")
                else:
                    messages.error(request, f"Wrong Destination. Ticket is for {ticket.end_station}.")
            
            elif ticket.status == Ticket.Status.EXPIRED:
                messages.error(request, "Ticket already used.")

        except Ticket.DoesNotExist:
            messages.error(request, "Ticket not found.")

    return render(request, 'scanner_dashboard.html', {'station_name': scanner_location})

