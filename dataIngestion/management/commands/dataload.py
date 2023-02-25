from django.core.management.base import BaseCommand
from dataIngestion.models import import_Data,importSources

class Command(BaseCommand):
    help='load data into task types'

    def handle(self,*args,**kwargs):
        import_Data.objects.all().delete()
        importSources.objects.all().delete()
        sources= ["Import from database","Import from cloud"]

        if not importSources.objects.count():
            for source in sources:
                importSources.objects.create(name=source)


        ## For database
        db_object=importSources.objects.get(name='Import from database')

        db_types=["MySql","Cassandra","MongoDB"]

        for type in db_types:
            import_Data.objects.create(name=type,import_sources=db_object)


        ## For cloud
        cloud_object=importSources.objects.get(name='Import from cloud')

        cloud_types=['AWS S3 Bucket','GCP Blob Storage','Azure Data Storage']

        for outl in cloud_types:
            import_Data.objects.create(name=outl,import_sources=cloud_object)
