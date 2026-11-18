from django.core.management.base import BaseCommand
from academy.models import Resource
from academy.rag import index_resource
class Command(BaseCommand):
    help='Rebuild document chunks and embeddings from all uploaded originals.'
    def handle(self,*args,**options):
        for resource in Resource.objects.all(): self.stdout.write(f'{resource.pk}: {"ready" if index_resource(resource) else "failed"}')
