"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.contrib import admin
from django.urls import path, include

# Configurable so the admin login isn't sitting at the one path every
# credential-stuffing bot scans by default. Unset -> unchanged 'admin/'.
ADMIN_URL_PATH = os.environ.get('ADMIN_URL_PATH', 'admin/').lstrip('/')
if not ADMIN_URL_PATH.endswith('/'):
    ADMIN_URL_PATH += '/'

urlpatterns = [
    path(ADMIN_URL_PATH, admin.site.urls),
    path('api/', include('inquiries.urls')),
]
