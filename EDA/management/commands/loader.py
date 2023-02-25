from django.core.management.base import BaseCommand
from EDA.models import TaskType,plot_Data

class Command(BaseCommand):
    help='load data into task types'

    def handle(self,*args,**kwargs):
        plot_Data.objects.all().delete()
        TaskType.objects.all().delete()
        task_types=[
            'Regular Plots','Correlation plots','Outlier Detection plots'
        ]

        if not TaskType.objects.count():
            for tasks in task_types:
                TaskType.objects.create(name=tasks)


        ## regular plots
        numeric_object=TaskType.objects.get(name='Regular Plots')

        num_data_modes=['boxplot','pieplot', 'barplot','scatterplot','violinplot','distplot', 'lineplot','histogram']

        for num in num_data_modes:
            plot_Data.objects.create(name=num,task_type=numeric_object)


        ## correlation plots
        correlation_object=TaskType.objects.get(name='Correlation plots')

        corr_data_modes=['heatmap','pairplot']

        for corr in corr_data_modes:
            plot_Data.objects.create(name=corr,task_type=correlation_object)


        ## outlier plots
        outlier_object=TaskType.objects.get(name='Outlier Detection plots')

        outl_data_modes=['scatterplot','boxplot','barplot']

        for outl in outl_data_modes:
            plot_Data.objects.create(name=outl,task_type=outlier_object)
