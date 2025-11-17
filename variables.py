import os
from mysql_database import DatabaseCreds

db_creds = DatabaseCreds(os.getenv("DB_HOST"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), port=os.getenv("DB_PORT"))