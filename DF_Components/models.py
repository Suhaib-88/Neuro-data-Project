from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from django.conf import settings



class DataFlowComponent(models.Model):
    name=models.CharField(max_length=120,unique=False)
    urls=models.CharField(max_length=50,unique=True, null=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='components')

    def __str__(self):
        return self.name

class UserComponents(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    components = models.ForeignKey(DataFlowComponent, on_delete=models.CASCADE)