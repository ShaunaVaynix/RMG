from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # built-in login/logout
    path('', include('todo.urls')),      # reservation/dashboard
    path('pc/', include('pc_login.urls')),  # pc login
]