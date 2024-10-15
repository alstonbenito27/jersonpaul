import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/event_photography'

    # MAIL_SERVER = 'smtp-mail.outlook.com'
    # MAIL_PORT = 587
    # MAIL_USE_TLS = True
    # MAIL_USERNAME = 'notanothersite@outlook.com'  # Your Gmail address
    # MAIL_PASSWORD = 'Alston@27'  # Your App Password
    # MAIL_DEFAULT_SENDER = 'notanothersite@outlook.com'