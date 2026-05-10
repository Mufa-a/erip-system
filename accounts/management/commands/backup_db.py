import os
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from decouple import config


class Command(BaseCommand):
    help = 'Backup PostgreSQL database'

    def handle(self, *args, **kwargs):
        db_name = config('DB_NAME', default='erp_db')
        db_user = config('DB_USER', default='postgres')
        db_pass = config('DB_PASSWORD', default='')
        db_host = config('DB_HOST', default='localhost')
        db_port = config('DB_PORT', default='5432')

        timestamp   = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir  = 'backups'
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = f"{backup_dir}/erp_backup_{timestamp}.sql"

        os.environ['PGPASSWORD'] = db_pass

        pg_dump = f'"C:\\Program Files\\PostgreSQL\\18\\bin\\pg_dump.exe"'
        cmd = f'{pg_dump} -h {db_host} -p {db_port} -U {db_user} -F c -b -f {backup_file} {db_name}'

        try:
            os.system(cmd)
            self.stdout.write(self.style.SUCCESS(f'✅ Backup saved: {backup_file}'))

            # Cleanup old backups (keep last 7)
            files = sorted([
                f for f in os.listdir(backup_dir) if f.endswith('.sql')
            ])
            while len(files) > 7:
                old = os.path.join(backup_dir, files.pop(0))
                os.remove(old)
                self.stdout.write(f'🗑 Deleted old backup: {old}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Backup failed: {e}'))