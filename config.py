import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///redshift.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Mail config 
    MAIL_SERVER = 'smtp.fastmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') #os.environ.get('MAIL_USERNAME')  # Your email
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # App-specific password
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
