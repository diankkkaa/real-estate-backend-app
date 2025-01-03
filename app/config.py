import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        "mssql+pyodbc://@localhost/RealEstate?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12) 
