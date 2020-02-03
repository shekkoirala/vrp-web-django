from django.contrib.auth.models import User
from django.core.management import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            admin = User.objects.create_superuser(
                email='admin@admin.com',
                username='admin')
            admin.set_password('admin1234')
            admin.is_active = True
            admin.is_admin = True
            admin.save()
            print("Successfully created admin")
        except:
            print("Admin already exists")

