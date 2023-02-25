from django.core.management.base import BaseCommand
from dataProcessing.models import export_Data,exportSources

class Command(BaseCommand):
    help='load data into task types'

    def handle(self,*args,**kwargs):
        # plot_Data.objects.all().delete()
        # exportSources.objects.all().delete()
        sources= ["Export to file","Export to database","Export to cloud"]

        if not exportSources.objects.count():
            for source in sources:
                exportSources.objects.create(name=source)


        ## For Files
        file_export_object=exportSources.objects.get(name='Export to file')

        file_types=['csv','tsv','json','xlsx']

        for type in file_types:
            export_Data.objects.create(name=type,export_sources=file_export_object)


        ## For database
        db_object=exportSources.objects.get(name='Export to database')

        db_types=["MySql","Cassandra","MongoDB"]

        for type in db_types:
            export_Data.objects.create(name=type,export_sources=db_object)


        ## For cloud
        cloud_object=exportSources.objects.get(name='Export to cloud')

        cloud_types=['AWS S3 Bucket','GCP Blob Storage','Azure Data Storage']

        for outl in cloud_types:
            export_Data.objects.create(name=outl,export_sources=cloud_object)
