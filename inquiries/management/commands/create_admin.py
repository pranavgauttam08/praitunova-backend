from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = 'Create a superuser from environment variables (safe to run multiple times)'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'pgkijai301@gmail.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')

        if not password:
            self.stdout.write(self.style.ERROR('DJANGO_SUPERUSER_PASSWORD env var not set. Skipping.'))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists. Skipping.'))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))
