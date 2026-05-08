from django.core.management.base import BaseCommand
from core.backup import backup_database, cleanup_old_backups


class Command(BaseCommand):
    help = 'Backup the database'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database backup...')
        result = backup_database()
        if result:
            self.stdout.write(
                self.style.SUCCESS(f'Backup complete: {result}')
            )
            cleanup_old_backups(keep_days=7)
        else:
            self.stdout.write(
                self.style.ERROR('Backup failed!')
            )