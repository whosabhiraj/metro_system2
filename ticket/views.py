from django.shortcuts import render
from .forms import TicketForm, RegistrationForm, AddMoneyForm
from .models import Ticket, Line, ScannerProfile, ThroughTable, OTP
from django.shortcuts import get_object_or_404, redirect
import metro_orm as fare
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
import datetime, random, os, sys
from django.utils import timezone
from django.core.mail import send_mail

directory_path = os.path.abspath("F:/code/djangolearn/metro_system/")
sys.path.append(directory_path)

# Create your views here.


def index(request):
    return render(request, "index.html")


@login_required
def ticket_list(request):
    # if ScannerProfile:
    #     return redirect("scanner")
    # else:

    tickets = Ticket.objects.all()
    for ticket in tickets:
        if ticket.created_at + datetime.timedelta(days=1) < timezone.now():
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
                    )

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
                print(sent_otp.code)  # for testing

                request.session["sent_otp"] = sent_otp.pk
                request.session["ticket_price"] = generated_ticket.price

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
        request.user.balance += ticket.price
        ticket.delete()
        request.user.save()
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
                if ticket.start_station == scanner_location.id:
                    ticket.status = Ticket.Status.IN_USE
                    ticket.save()
                    messages.success(
                        request, f"Entry Approved at {scanner_location.name}!"
                    )
                else:
                    messages.error(
                        request, f"Wrong Station. Ticket is for {ticket.start_station}."
                    )

            elif ticket.status == Ticket.Status.IN_USE:
                if ticket.end_station == scanner_location.id:
                    ticket.status = Ticket.Status.USED
                    ticket.save()
                    messages.success(
                        request, f"Exit Approved at {scanner_location.name}!"
                    )
                else:
                    messages.error(
                        request,
                        f"Wrong Destination. Ticket is for {ticket.end_station}.",
                    )

            elif ticket.status == Ticket.Status.EXPIRED:
                messages.error(request, "Ticket already used.")

        except Ticket.DoesNotExist:
            messages.error(request, "Ticket not found.")

    return render(
        request, "scanner_dashboard.html", {"station_name": scanner_location.name}
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


# request response cycle
# docker
# authentication/authoriszation
# edge case
# drop down hogya
# otp hogya
# through table hogya
# ngnix
# django orm
