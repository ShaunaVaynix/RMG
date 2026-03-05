from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/user/', views.user_dashboard, name='user_dashboard'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Main pages
    # Admin computers
    path('computers/', views.computers_view, name='computers'),
    # User computers
    path('user/computers/', views.user_computers, name='user_computers'),
    path('users/', views.users_view, name='users'),
  # Main pages
    path('reservation/', views.reserve_view, name='reservation'),          # Admin reservations
    path('user/reservation/', views.user_reservation, name='user_reservation'),  # User reservations

    # API endpoints
    path('api/get_computers_json/', views.get_computers_json, name='get_computers_json'),
    path('api/add_computer/', views.add_computer, name='add_computer'),
    path("api/delete_computer/<str:pc_id>/", views.delete_computer, name="delete_computer"),
    path('api/get_reservations_json/', views.get_reservations_json, name='get_reservations_json'),
    path('api/add_reservation/', views.add_reservation, name='add_reservation'),

    path('user/payment/', views.payment_view, name='payment'),
]