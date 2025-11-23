from . import views
from django.urls import path, include

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.ticket_create, name='ticket_create'),
    path('<int:ticket_id>/cancel/', views.ticket_cancel, name='ticket_cancel'),
    path('register/', views.register, name='register'),
    path('add_money/', views.add_money, name='add_money'),
    path('insufficient_balance/', views.insufficient_balance, name='insufficient_balance'),
    path('scanner/', views.scan_ticket, name='scanner'),
    path('index', views.index, name='index'),
    # path('accounts/', include('allauth.urls')), THIS CAUSED AN ISSUE
]