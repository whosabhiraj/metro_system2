from . import views
from django.urls import path, include

urlpatterns = [
    path("", views.ticket_list, name="ticket_list"),
    path("create/", views.ticket_create, name="ticket_create"),
    path("<int:ticket_id>/cancel/", views.ticket_cancel, name="ticket_cancel"),
    path("register/", views.register, name="register"),
    path("add_money/", views.add_money, name="add_money"),
    path("insufficient_balance/", views.insufficient_balance, name="insufficient_balance"),
    path("scanner/", views.scan_ticket, name="scanner"),
    path("index/", views.index, name="index"),
    path("map/", views.ticket_map, name="ticket_map"),
    path("admin/", views.admin, name="admin"),
    path("admin/add_line/", views.add_line, name="add_line"),
    path("admin/add_station/", views.add_station, name="add_station"),
    path("admin/link_station/", views.link_station, name="link_station"),  # type: ignore
    path("admin/service_toggle/", views.service_toggle, name="service_toggle"),  # type:ignore
    path("scanner/offline_ticket/", views.offline_ticket, name="offline_ticket"), # type: ignore
    path("admin/delete_station/", views.delete_station, name="delete_station"),  # type: ignore
    # path('accounts/', include('allauth.urls')), THIS CAUSED AN ISSUE
]
