from django.db import models


# Create your models here.

class TaskType(models.Model):
    name= models.CharField(max_length=50)
    
    def __str__(self):
        return self.name


# class ChartType(models.Model):
#     task_type=models.ForeignKey(TaskType,on_delete=models.CASCADE)
#     name= models.CharField(max_length=30)

#     def __str__(self):
#         return self.name


class plot_Data(models.Model):
    name= models.CharField(max_length=50)
    task_type= models.ForeignKey(TaskType,on_delete=models.SET_NULL,null=True,related_name='plotting') 

    def __str__(self):
        return "{0}".format(str(self.name))