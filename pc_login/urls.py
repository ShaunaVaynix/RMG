from django.urls import path
from . import views

urlpatterns = [
    path('', views.pc_login_page, name='pc_login'),
    path('api/', views.pc_login_api, name='pc_login_api'),
    path('dashboard/', views.pc_dashboard, name='pc_dashboard'),
]