from flask import *
from flask_mail import *

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'live.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'api'
app.config['MAIL_PASSWORD'] = '154cc83fc9fb972af7a760cbbb57f593'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)


@app.route('/send')
def send():
    message = Message(
        subject = "Hi",
        recipients = ['alstonbenito027@gmail.com'],
        sender = 'alstonbeny@gmail.com'
    )
    message.body = "hello"
    mail.send(message)
    return "Message sent!"
