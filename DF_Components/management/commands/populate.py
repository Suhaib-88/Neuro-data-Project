from django.core.management.base import BaseCommand
from DF_Components.models import DataFlowComponent,UserComponents

class Command(BaseCommand):
    help='load data into task types'

    def handle(self,*args,**kwargs):
        DataFlowComponent.objects.all().delete()
        UserComponents.objects.all().delete()
        # component_list=[
        #     'Import data from DataBase','Import data from File upload','Import data from Cloud','Aggregate Component',
        #     'Row Counter Component','Character Map Component','Conditional-split Component',
        # ]
        # component_url_list=['import-db','import-file','import-cloud','aggregator','counter','map','conditional']

        # if not DataFlowComponent.objects.count():
        #     for url,component in zip(component_url_list,component_list):
        #         DataFlowComponent.objects.create(urls=url,name=component)