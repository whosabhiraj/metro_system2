from django.shortcuts import render
from .forms import TicketForm, RegistrationForm, AddMoneyForm
from .models import Ticket, Station, Line, ScannerProfile, ThroughTable, OTP, FootFall, ServiceStatus, CustomUser
from django.shortcuts import get_object_or_404, redirect
from . import metro_orm as fare
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, get_user_model
from django.contrib import messages
import datetime, random
from django.utils import timezone
from django.core.mail import send_mail

# Create your views here.


def index(request):
    return render(request, "index.html")


@login_required
def ticket_list(request):
    if ServiceStatus.objects.exists():
        service_status = ServiceStatus.objects.first().active # type: ignore
        # print(service_status)
        if not service_status:
            return render(request, "outofservice.html")
    try:
        profile = ScannerProfile.objects.get(user=request.user)
        if profile:
            return redirect('scanner')
        
    except ScannerProfile.DoesNotExist:
        pass
    
    tickets = Ticket.objects.filter(user=request.user)
    for ticket in tickets:
        if ticket.created_at + datetime.timedelta(days = 1) < timezone.now():
            ticket.status = ticket.Status.EXPIRED
            ticket.save()
    return render(request, "ticket_list.html", {"tickets": tickets})


def ticket_create(request):
    form = TicketForm(request.POST)

    if request.method == "POST":
        if form.is_valid():

            start_station = form.cleaned_data["start_station"]
            end_station = form.cleaned_data["end_station"]
            input_otp = form.cleaned_data.get("otp")

            # verifying otp if otp was submitted
            if input_otp:
                saved_otp_id = request.session.get("sent_otp")
                saved_otp = OTP.objects.get(id=saved_otp_id)
                saved_price = request.session.get("ticket_price")

                if (saved_otp and int(input_otp) == saved_otp.code and saved_otp.created_at + datetime.timedelta(minutes=15) > timezone.now()):
                    # case otp matches and is active
                    saved_otp.delete()

                    request.user.balance -= saved_price
                    request.user.save()

                    Ticket.objects.create(
                        user=request.user,
                        start_station=start_station,
                        end_station=end_station,
                        price=saved_price,
                        uid=request.session['uid'],
                    )

                    del request.session["uid"]
                    del request.session["sent_otp"]
                    del request.session["ticket_price"]
                    
                    return redirect("ticket_list")
                elif (saved_otp.created_at + datetime.timedelta(minutes=15) < timezone.now()):
                    # case otp expired
                    saved_otp.delete()
                    messages.error(request, "OTP expired. Please try again.")
                else:
                    # case otp invalid
                    saved_otp.delete()
                    messages.error(request, "Invalid OTP.")

            # validate stations and generate otp
            else:
                try:
                    generated_ticket = fare.metro_system().generate_ticket(start_station.id, end_station.id)
                except fare.NoPathError:
                    messages.error(request, "No path between stations.")
                    return redirect("ticket_create")
                except fare.ZeroPathError:
                    messages.error(request, "Please select two distinct stations.")
                    return redirect("ticket_create")
                if request.user.balance < generated_ticket.price:
                    return render(request, "insufficient_balance.html")

                sent_otp = OTP(code=random.randint(100000, 999999))
                sent_otp.save()
                # print(sent_otp.code)  # for testing

                request.session["sent_otp"] = sent_otp.pk
                request.session["ticket_price"] = generated_ticket.price
                request.session["uid"] = generated_ticket.id

                send_mail(
                    subject="Metro system OTP",
                    message=f"OTP for your ticket \n From: {start_station.name} \n To: {end_station.name} \n Price: {generated_ticket.price} \n Code: {sent_otp.code} \n OTP valid upto 15 minutes.",
                    recipient_list=[request.user.email],
                    from_email="metrosystem.otp@gmail.com",
                )

                messages.success(request, f"OTP sent to email.")

                # render same page again and otp_sent is true so above block executes
                return render(
                    request,
                    "ticket_form.html",
                    {
                        "form": form,
                        "otp_sent": True,
                        "ticket_price": generated_ticket.price,
                    },  # pass this for html so otp confirm page is shown instead of station select
                )

    return render(request, "ticket_form.html", {"form": form})


@login_required
def ticket_cancel(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    if request.method == "POST":
        if ticket.Status == 'ACTIVE':
            request.user.balance += ticket.price
            ticket.delete()
            request.user.save()
        else:
            messages.error(request, "You can only cancel active tickets.")
        return redirect("ticket_list")
    return render(request, "ticket_confirm_cancel.html", {"ticket": ticket})


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")  # type: ignore
        redirect("ticket_list")
    else:
        form = RegistrationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def add_money(request):
    if request.method == "POST":
        form = AddMoneyForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]
            request.user.balance += amount
            request.user.save()
            return redirect("ticket_list")
    else:
        form = AddMoneyForm()

    return render(request, "add_money.html", {"form": form})


def insufficient_balance(request):
    return render(request, "insufficient_balance.html")


@login_required
def scan_ticket(request):
    try:
        profile = ScannerProfile.objects.select_related("station").get(
            user=request.user
        )
        scanner_location = profile.station

    except ScannerProfile.DoesNotExist:
        messages.error(request, "Access Denied: Unauthorized")
        return redirect("index")

    if request.method == "POST":
        uid = request.POST.get("ticket_uid").strip()

        try:
            ticket = Ticket.objects.get(uid=uid)

            if ticket.status == Ticket.Status.ACTIVE:
                if ticket.start_station.id == scanner_location.id:
                    ticket.status = Ticket.Status.IN_USE
                    ticket.save()
                    footfall = FootFall.objects.filter(station=scanner_location, date=datetime.date.today()).first()
                    if not footfall:
                        footfall = FootFall(station=scanner_location, date=datetime.date.today(), into=1, out=0)
                    else:
                        footfall.into += 1
                    footfall.save()
                    messages.success(
                        request, f"Entry Approved at {scanner_location.name}!"
                    )
                else:
                    messages.error(
                        request, f"Wrong Station. Ticket is for {ticket.start_station}."
                    )

            elif ticket.status == Ticket.Status.IN_USE:
                if ticket.end_station.id == scanner_location.id:
                    ticket.status = Ticket.Status.USED
                    ticket.save()
                    footfall = FootFall.objects.filter(station=scanner_location, date=datetime.date.today()).first()
                    if not footfall: # if no entry is found, entry is made
                        footfall = FootFall(station=scanner_location, date=datetime.date.today(), into=0, out=1)
                    else: # if entry is found, count is incremented
                        footfall.out += 1
                    footfall.save()
                    messages.success(
                        request, f"Exit Approved at {scanner_location.name}!"
                    )
                else:
                    messages.error(
                        request,
                        f"Wrong Destination. Ticket is for {ticket.end_station}.",
                    )

            elif ticket.status == Ticket.Status.EXPIRED:
                messages.error(request, "Ticket expired.")

        except Ticket.DoesNotExist:
            messages.error(request, "Ticket not found.")

    context = {
        'is_scanner': True,
        "station_name": scanner_location.name,
    }

    return render(
        request, "scanner_dashboard.html", context
    )


def ticket_map(request):
    lines = Line.objects.all()
    map = []

    for line in lines:
        line_stations = (
            ThroughTable.objects.filter(line=line)
            .select_related("station")
            .order_by("order")
        )

        stations_list = [link.station for link in line_stations]

        map.append({"line": line, "stations": stations_list})

    context = {"map": map}
    return render(request, "map.html", context)


@login_required
def admin(request):
    if request.user.is_superuser:
        date = request.GET.get("date")
        lines = Line.objects.all()
        stations = Station.objects.all()
        map = []

        for line in lines:
            line_stations = (
                ThroughTable.objects.filter(line=line)
                .select_related("station")
                .order_by("order")
            )

            stations_list = [link.station for link in line_stations]

            map.append({"line": line, "stations": stations_list})

        context = {
            'footfall_data': FootFall.objects.filter(date=date) if date else None,
            'lines': lines,
            'stations': stations,
            'map': map,
            'service_status': ServiceStatus.objects.first().active if ServiceStatus.objects.exists() else True, # type: ignore
        }
        return render(request, 'admin.html', context)
    else:
        messages.error(request, 'User unauthorised')
        return redirect("index")
    

def add_line(request):
    if request.method == "POST":
        name = request.POST.get('line_name')
        if Line.objects.filter(name=name).exists():
            messages.error(request, 'Line with this name already exists')
            return redirect('admin')
        # print(name)
        Line.objects.create(name=name)
        return redirect('admin')
    return redirect('admin')

def add_station(request):
    if request.method == "POST":
        name = request.POST.get('station_name')
        # print(name)
        order = int(request.POST.get('order'))
        line_obj = Line.objects.get(id=request.POST.get('line'))
        # print(line_obj)

        if order > ThroughTable.objects.filter(line_id=line_obj.id).count()+1:
            messages.error(request, 'Invalid order: exceeds number of stations in line')
            return redirect('admin')
        if Station.objects.filter(name=name).exists():
            messages.error(request, 'Station with this name already exists')
            return redirect('admin')
        
        stations_on_line = ThroughTable.objects.filter(line_id=line_obj.id).count()
        while order < stations_on_line + 1: # create space to insert station into line
            ThroughTable.objects.filter(line=line_obj, order=stations_on_line).update(order=stations_on_line+1)
            stations_on_line -= 1
        
        Station.objects.create(name=name)
        ThroughTable.objects.create(
            line=line_obj,
            station=Station.objects.get(name=name),
            order=order
        )
        return redirect('admin')
    return redirect('admin')

def link_station(request):
    if request.method == 'POST':
        pass
        station_obj = Station.objects.get(id=request.POST.get('station_id'))
        line_obj = Line.objects.get(id=request.POST.get('line_id'))
        order = int(request.POST.get('order'))
        stations_on_line = ThroughTable.objects.filter(line_id=line_obj.id).count()

        if order > stations_on_line + 1:
            messages.error(request, 'Invalid order: exceeds number of stations in line')
            return redirect('admin')
        
        while order < stations_on_line + 1: # create space to insert station into line
            ThroughTable.objects.filter(line=line_obj, order=stations_on_line).update(order=stations_on_line+1)
            stations_on_line -= 1

        ThroughTable.objects.create(
            line=line_obj,
            station=station_obj,
            order=order
        )
        return redirect('admin')
    

def delete_station(request):
    if request.method == "POST":
        station_id = request.POST.get('station_id')

        station_obj = Station.objects.get(id=station_id)
        affected_links = ThroughTable.objects.filter(station=station_obj)

        affected_links.delete()
        for link in affected_links:
            current_line = link.line
            removed_order = link.order
            for order in range(removed_order + 1, ThroughTable.objects.filter(line=current_line).count() + 1):
                ThroughTable.objects.filter(line=current_line, order=order).update(order=order - 1)
        
        messages.success(request, f'Station "{station_obj.name}" removed and subsequent stations shifted.')
        return redirect('admin')

    return redirect('admin')
    

def service_toggle(request):
    if request.method == 'POST':
        status = request.POST.get('service_status') == True
        if ServiceStatus.objects.exists():
            service_status = ServiceStatus.objects.first()
            service_status.active = not service_status.active # type: ignore
            service_status.save() # type: ignore
        else:
            ServiceStatus.objects.create(active=status)
        return redirect('admin')
    

def offline_ticket(request):
    if request.method == 'POST':
        start_station = ScannerProfile.objects.get(user=request.user).station
        user = CustomUser.objects.get(username=request.POST.get('username'))
        # print(request.POST.get('username'))
        # print(request.POST.get('end_station'))
        end_station = Station.objects.get(pk=request.POST.get('end_station'))
        # print(end_station)

        try:
            ticket = fare.metro_system().generate_ticket(start_station.id, end_station.id)
        except fare.NoPathError:
            messages.error(request, f"No path to {end_station.name}.")
            return redirect("offline_ticket")
        except fare.ZeroPathError:
            messages.error(request, "Please select a different station.")
            return redirect("offline_ticket")

        Ticket.objects.create(
            user=user,
            start_station=start_station,
            end_station=end_station,
            price=ticket.price,
            uid=ticket.id,
            status=Ticket.Status.IN_USE,
        )
        messages.success(request, f'Offline ticket issued to {user.username} from {start_station.name} to {end_station.name} at price {ticket.price}')

        send_mail(
                subject="Metro system Offline Ticket Issued",
                message=f"Offline ticket issued \n From: {start_station.name} \n To: {end_station.name} \n Price: {ticket.price} \n Ticket UID: {ticket.id} \n Please pay at the counter.",
                recipient_list=[user.email],
                from_email="metrosystem.otp"
        )

    context = {
        'is_scanner': True,
        'stations': Station.objects.all(),
        'station_name': ScannerProfile.objects.get(user=request.user).station.name,
    }
    return render(request, 'offline_ticket.html', context)
