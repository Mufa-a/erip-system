import os
import subprocess
from datetime import datetime
from decouple import config


def backup_database():
    db_name   = config('DB_NAME', default='erp_db')
    db_user   = config('DB_USER', default='postgres')
    db_pass   = config('DB_PASSWORD', default='')
    db_host   = config('DB_HOST', default='localhost')
    db_port   = config('DB_PORT', default='5432')

    timestamp   = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir  = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = f"{backup_dir}/erp_backup_{timestamp}.sql"

    os.environ['PGPASSWORD'] = db_pass

    cmd = [
        'pg_dump',
        '-h', db_host,
        '-p', db_port,
        '-U', db_user,
        '-F', 'c',
        '-b',
        '-v',
        '-f', backup_file,
        db_name
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Backup saved: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        print(f"❌ Backup failed: {e}")
        return None


def cleanup_old_backups(keep_days=7):
    import time
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        return
    now = time.time()
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath):
            age_days = (now - os.path.getmtime(filepath)) / 86400
            if age_days > keep_days:
                os.remove(filepath)
                print(f"🗑 Deleted old backup: {filename}")