from django.core.management.base import BaseCommand

from main.services.parsers import parse_mospolytech_group_schedule
from main.models import StudentGroup


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('group', type=str)
        parser.add_argument('token', type=str)

    def handle(self, *args, **options):
        self.parse_group_schedule(options['group'], options['token'])

    def parse_group_schedule(self, group: str, token: str):
        group_obj = StudentGroup.objects.get(name=group)
        parse_mospolytech_group_schedule(group_obj, token)
