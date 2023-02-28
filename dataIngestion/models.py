from django.db import models
from .choice import PROBLEM_TYPES_LIST
from django.contrib.auth.models import User

# Create your models here.

class importSources(models.Model):
    name= models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

class import_Data(models.Model):
    name= models.CharField(max_length=50,null=True)
    import_sources= models.ForeignKey(importSources,on_delete=models.SET_NULL,null=True,related_name='sources') 


class upload_Dataset(models.Model):
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    problem_statement_type= models.CharField(max_length=20,choices=PROBLEM_TYPES_LIST) #
    problem_statement_name = models.CharField(max_length=40,null=True)
    problem_statement_description = models.TextField(max_length=75,null=True,blank=True)
    file_upload = models.FileField(upload_to='./uploads/',null=True,blank=True)
    upload_date= models.DateTimeField(auto_now_add=True,null=True)
    Last_modified= models.DateTimeField(auto_now=True,null=True)
    file_from_resources=models.CharField(max_length=50,null=True)
    
    def __str__(self):
        return self.problem_statement_name


