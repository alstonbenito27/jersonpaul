import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/event_photography'

    # Mail configuration
    MAIL_SERVER = 'live.smtp.mailtrap.io'
    MAIL_PORT = 587
    MAIL_USERNAME = 'api'  # Your Mailtrap username
    MAIL_PASSWORD = '154cc83fc9fb972af7a760cbbb57f593'  # Your Mailtrap password
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False