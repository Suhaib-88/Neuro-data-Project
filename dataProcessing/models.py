from django.db import models
# Create your models here.

    
class exportSources(models.Model):
    name= models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

class export_Data(models.Model):
    name= models.CharField(max_length=50)
    export_sources= models.ForeignKey(exportSources,on_delete=models.SET_NULL,null=True,related_name='sources') 

    def __str__(self):
        return "{0}".format(str(self.name))
