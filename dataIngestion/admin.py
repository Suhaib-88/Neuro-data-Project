from django.contrib.admin.sites import site
from django.contrib import admin

from dataIngestion.models import upload_Dataset

# Register your models here.

admin.site.register(upload_Dataset)