import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session,jsonify
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from app import mongo
from pymongo import MongoClient
import gridfs
from config import Config
from flask_mail import Message
from app import mail
import requests
from sendgrid.helpers.mail import Mail
from datetime import datetime
from instamojo_wrapper import Instamojo
from twilio.rest import Client
import smtplib
import random
from email.mime.text import MIMEText
import smtplib
from email.message import EmailMessage
import braintree



home_bp = Blueprint('home', __name__)
admin_bp = Blueprint('admin', __name__)

api = Instamojo(api_key='a209577391ea0a4b164177cc0cf12393', auth_token='6cf8e4581a8eeae7eddca244b2b855ca', endpoint='https://test.instamojo.com/api/1.1/')

account_sid = 'AC96ec7124a4da4314afcd0e7dcf74552d'
auth_token = '38294efb5176466aedb14c31b5bb772f'
verify_service_sid = 'VAae710ac474440b664420106ebe0db63b'

client = Client(account_sid, auth_token)

gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=braintree.Environment.Sandbox,  # Use 'Production' for live
        merchant_id='8wqh62pkncmc9y4h',
        public_key='kb8kqgnzncb8k3jw',
        private_key='8e23ef18c6e2b8fe624e2185874e54cc'
    )
)

UPLOAD_FOLDER = r'E:\Mini Project\THEPROJECTC\app\static\uploads\gallery'

# MongoDB connection using config
mongo_client = MongoClient(Config.MONGO_URI)
db = mongo_client['event_photography'] # Replace with your actual database name
gallery_fs = gridfs.GridFS(db, collection='gallery')

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home page route
@home_bp.route('/')
def home():
    # Define paths for categories
    wedding_images = os.listdir(os.path.join(UPLOAD_FOLDER, 'wedding'))
    corporate_images = os.listdir(os.path.join(UPLOAD_FOLDER, 'corporate'))
    house_festivities_images = os.listdir(os.path.join(UPLOAD_FOLDER, 'house_festivities'))

    return render_template(
        'home.html',
        wedding_images=wedding_images,
        corporate_images=corporate_images,
        house_festivities_images=house_festivities_images,
        gallery_folder=UPLOAD_FOLDER  # pass the gallery folder path
    )
# Admin login page route
@admin_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = mongo.db.admin.find_one({"username": username})
        if admin and admin['password'] == password: # Assuming plain text for testing
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('admin_login.html')
@admin_bp.route('/admin/logout')
def logout():
    # Remove all the session data (logout the user)
    session.clear()
    # Redirect to the home page
    return redirect(url_for('home.home'))

# Admin dashboard route
@admin_bp.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

# Admin services route
@admin_bp.route('/admin_services', methods=['GET', 'POST'])
def admin_services():
    if request.method == 'POST':
        service_id = request.form.get('service_id')
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        price = request.form.get('price')
        advance = request.form.get('advance')

        # Input validation
        if not name or not description or not category or not price or not advance:
            flash('All fields are required.')
            return redirect(url_for('admin.admin_services'))

        try:
            price = float(price)
            advance = float(advance)
        except ValueError:
            flash('Price and advance must be valid numbers.')
            return redirect(url_for('admin.admin_services'))

        if service_id:  # Update existing service
            mongo.db.services.update_one(
                {'_id': ObjectId(service_id)},
                {'$set': {
                    'name': name,
                    'description': description,
                    'category': category,
                    'price': price,
                    'advance': advance
                }}
            )
            flash('Service updated successfully')
        else:  # Add new service
            mongo.db.services.insert_one({
                'name': name,
                'description': description,
                'category': category,
                'price': price,
                'advance': advance
            })
            flash('Service added successfully')

        return redirect(url_for('admin.admin_services'))

    # Handling service deletion
    delete_service_id = request.args.get('delete_service_id')
    if delete_service_id:
        mongo.db.services.delete_one({'_id': ObjectId(delete_service_id)})
        flash('Service deleted successfully')
        return redirect(url_for('admin.admin_services'))

    # Fetch all services and convert cursor to a list to avoid exhaustion
    services = list(mongo.db.services.find())

    # Categorizing services into lists for display
    wedding_services = [svc for svc in services if svc['category'] == 'Wedding']
    corporate_services = [svc for svc in services if svc['category'] == 'Corporate']
    house_festivities_services = [svc for svc in services if svc['category'] == 'House Festivities']

    # Check if we are editing a service
    service_id = request.args.get('service_id')
    service = mongo.db.services.find_one({'_id': ObjectId(service_id)}) if service_id else None

    return render_template(
        'admin_services.html',
        wedding_services=wedding_services,
        corporate_services=corporate_services,
        house_festivities_services=house_festivities_services,
        service=service
    )


@admin_bp.route('/image/<file_id>')
def serve_image(file_id):
    # Retrieve image by its ID
    image = gallery_fs.get(ObjectId(file_id))

    # Return the file content with the correct content type
    return send_file(image, mimetype=image.content_type)


# Admin gallery route
@admin_bp.route('/admin_gallery', methods=['GET', 'POST'])
def admin_gallery():
    if request.method == 'POST':
        category = request.form.get('category')
        file = request.files.get('file')

        if category and file and allowed_file(file.filename):
            # Secure the filename
            filename = secure_filename(file.filename)
            # Create a category folder if it doesn't exist
            category_folder = os.path.join(UPLOAD_FOLDER, category)
            os.makedirs(category_folder, exist_ok=True)
            # Save the file to the specified folder
            file.save(os.path.join(category_folder, filename))
            flash(f'Image {filename} uploaded successfully!')
        else:
            flash('Invalid category or file!')

        return redirect(url_for('admin.admin_gallery'))

    # Fetch image filenames from the directory for each category
    wedding_images = os.listdir(os.path.join(UPLOAD_FOLDER, 'wedding'))
    corporate_images = os.listdir(os.path.join(UPLOAD_FOLDER, 'corporate'))
    house_festivities_images = os.listdir(os.path.join(UPLOAD_FOLDER, 'house_festivities'))

    return render_template(
        'admin_gallery.html',
        wedding_images=wedding_images,
        corporate_images=corporate_images,
        house_festivities_images=house_festivities_images
    )
# Admin delete image route
@admin_bp.route('/delete_image/<category>/<image_filename>', methods=['POST'])
def admin_delete_image(category, image_filename):
    try:
        # Construct the full path to the image
        image_path = os.path.join(UPLOAD_FOLDER, category, image_filename)

        # Check if the file exists, then delete it
        if os.path.exists(image_path):
            os.remove(image_path)
            flash(f'Image {image_filename} deleted successfully!')
        else:
            flash(f'Error: Image {image_filename} not found!')
    except Exception as e:
        flash(f'Error deleting image: {e}')

    return redirect(url_for('admin.admin_gallery'))

# Admin get image route
@admin_bp.route('/get_image/', endpoint='get_image_by_id')
def get_image(image_id):
    image = gallery_fs.find_one({'_id': ObjectId(image_id)})
    if image:
        return send_file(image, mimetype=image.content_type)
    else:
        flash('Image not found.')
        return redirect(url_for('admin.admin_gallery'))

# Admin details page route
@admin_bp.route('/admin_details')
def admin_details():
    return render_template('admin_details.html')

# Admin request page route
def send_email(subject, body):
    """Send an email to the specified recipient."""
    message = Message(
        subject=subject,
        sender='hello@demomailtrap.com',  # Your sender email
        recipients=['alstonbeny@gmail.com']  # Only this recipient
    )
    message.body = body
    try:
        mail.send(message)
    except Exception as e:
        print(f"Failed to send email: {str(e)}")


@admin_bp.route('/admin_request', methods=['GET', 'POST'])
def admin_request():
    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        status = request.form.get('status')  # 'Available' or 'Not Available'

        # Find the booking by ID
        booking = mongo.db.bookings.find_one({'_id': ObjectId(booking_id)})

        if booking:
            # Update booking status in the database
            mongo.db.bookings.update_one({'_id': ObjectId(booking_id)}, {'$set': {'status': status}})

            # Prepare email content
            subject = 'Booking Status Update'
            message_body = (
                f"Dear {booking['name']},\n\n"
                f"Thank you! Your booking for {booking['service_name']} on {booking['date']} is confirmed as {'available' if status == 'Available' else 'not available'}."
            )

            # Send email to the specified recipient
            send_email(subject, message_body)

            flash(f"Booking status updated and email sent to alstonbeny@gmail.com regarding status: {status}")
        else:
            flash('Booking not found.')

        return redirect(url_for('admin.admin_request'))

    # Fetch all bookings
    bookings = list(mongo.db.bookings.find())
    return render_template('admin_request.html', bookings=bookings)
# def send_test_email():
#     msg = Message('Test Email',
#                   sender='alstonbeny@gmail.com',
#                   recipients=['recipient@example.com'])
#     msg.body = 'This is a test email sent from Flask-Mail.'
#     mail.send(msg)

@home_bp.route('/services', methods=['GET'])
def services():
    category = request.args.get('category', 'Wedding')
    services = mongo.db.services.find({'category': category})
    categories = ['Wedding', 'Corporate', 'House Festivities']

    return render_template(
        'services.html',
        services=services,
        selected_category=category,
        categories=categories
    )


@home_bp.route('/book_services', methods=['GET', 'POST'])
def book_services():
    services = list(mongo.db.services.find())  # Fetch services for the form
    message = None  # Initialize message variable

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        service_name = request.form.get('service_name')  # Get the service name instead of ID
        date = request.form.get('date')

        # Check if the date is busy from the calendar collection
        busy_date = mongo.db.calendar.find_one({"date": date, "status": "busy"}) is not None

        if busy_date:
            message = "The selected date is busy. Please choose another date."
        else:
            # Insert booking with a pending status
            try:
                mongo.db.bookings.insert_one({
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "service_name": service_name,  # Save service name instead of ID
                    "date": date,
                    "status": "pending"  # Set status to pending
                })
                message = "Successfully booked! We will get back to you about confirmation soon."
            except Exception as e:
                message = "An error occurred while processing your booking. Please try again."

    return render_template('book_services.html', services=services, message=message)

# Gallery route
@home_bp.route('/gallery')
def gallery():
    # Code for gallery functionality
    pass


def generate_otp():
    """Generate a 6-digit OTP."""
    return random.randint(100000, 999999)


# def send_otp(email, otp):
#     msg = EmailMessage()
#     msg['Subject'] = 'Your OTP Code'
#     msg['From'] = 'alstonbeny@gmail.com'  # Replace with your email
#     msg['To'] = email
#     msg.set_content(f'Your OTP is {otp}. Please enter it to proceed.')
#
#     try:
#         with smtplib.SMTP('smtp.gmail.com', 587) as server:
#             server.starttls()
#             server.login('alstonbeny@gmail.com', 'nhkg eqlq xxcv fing')  # Replace with your email credentials
#             server.send_message(msg)
#     except Exception as e:
#         print(f"Failed to send email: {str(e)}")  # Log the error
#         raise  # Raise the exception to handle it in the route

# def test_send_email():
#     send_otp('alstonbenito027@gmail.com', "Your Service has been successfully booked. You will be contacted soon about further details.")  # Change to a valid email for testing
#
# # Call the test function
# test_send_email()

@home_bp.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        actual_otp = session.get('otp')

        print(f"Entered OTP: {entered_otp}, Actual OTP: {actual_otp}")  # Debug line

        if entered_otp == str(actual_otp):
            return redirect(url_for('home.payments'))
        else:
            flash('Invalid OTP. Please try again.', 'error')
            return redirect(url_for('home.verify_otp'))

    return render_template('verify_otp.html')


def generate_otp():
    """Generate a 6-digit OTP."""
    return random.randint(100000, 999999)

@home_bp.route('/service_form', methods=['GET', 'POST'])
def service_form():
    if request.method == 'GET':
        return render_template('service_form.html')

    if request.method == 'POST':
        selected_date = request.form.get('date')
        service_id = request.form.get('service_id')

        # Validate service ID
        if not service_id or len(service_id) != 24:
            flash("Invalid service ID.", 'error')
            return redirect(url_for('home.services'))

        # Check availability
        availability = mongo.db.calendar.find_one({'date': selected_date})

        if availability and availability['status'] == 'busy':
            flash("Date is busy. Please select another date.", 'error')
            return redirect(url_for('home.service_form'))

        # Retrieve service details
        service = mongo.db.services.find_one({'_id': ObjectId(service_id)})
        if not service:
            flash("Service not found.", 'error')
            return redirect(url_for('home.services'))

        service_name = service['name']
        advance = service['advance']

        # Render the payment page with the correct details
        return redirect(url_for('home.payments', service_name=service_name, advance=advance, selected_date=selected_date))


@home_bp.route('/payments', methods=['GET', 'POST'])
def payments():
    # Retrieve user details and service information from the session
    name = session.get('name')
    email = session.get('email')
    phone = session.get('phone')
    service_id = session.get('service_id')
    date = session.get('date')

    # Retrieve the selected service from MongoDB
    selected_service = mongo.db.services.find_one({'_id': ObjectId(service_id)})

    # Generate Braintree client token for frontend usage
    client_token = gateway.client_token.generate()

    if request.method == 'POST':
        # Get the Braintree payment method nonce from the form
        payment_method_nonce = request.form.get('payment_method_nonce')

        # Proceed with the payment using the advance amount of the selected service
        result = gateway.transaction.sale({
            'amount': str(selected_service['advance']),  # Advance amount as the payment amount
            'payment_method_nonce': payment_method_nonce,
            'options': {
                'submit_for_settlement': True  # Submit for immediate settlement
            }
        })

        if result.is_success:
            # If payment is successful, flash a success message and redirect
            flash("Payment successful.")
            return redirect(url_for('home.payment_success'))
        else:
            # Handle payment failure
            flash(f"Payment failed: {result.message}")
            return redirect(url_for('home.payments'))

    # Render the payments page with client token for Braintree Drop-In UI
    return render_template('payments.html', name=name, email=email, phone=phone, service=selected_service, date=date, client_token=client_token)

# Payment route

@home_bp.route('/process_payment', methods=['POST'])
def process_payment():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    advance = request.form.get('advance')
    service_name = request.form.get('service_name')

    # Create payment request
    response = api.payment_request_create(
        amount=advance,
        purpose=f"Payment for {service_name}",
        buyer_name=name,
        email=email,
        phone=phone,
        redirect_url="http://your_redirect_url.com/your_redirect_path"  # Update with your redirect URL
    )

    if response['success']:
        payment_url = response['payment_request']['longurl']
        return redirect(payment_url)
    else:
        flash('Payment request failed. Please try again.', 'error')
        return redirect(url_for('home.service_form'))


# Payment success route
@home_bp.route('/payment_success', methods=['GET'])
def payment_success():
    # Store payment details in MongoDB
    name = request.args.get('name')
    email = request.args.get('email')
    service_name = request.args.get('service_name')

    mongo.db.payments.insert_one({
        'name': name,
        'email': email,
        'service_name': service_name,
        'status': 'paid'
    })

    return "Payment Successful! Your booking is confirmed."


# Payment failure route
@home_bp.route('/payment_failure', methods=['GET'])
def payment_failure():
    return "Payment Failed. Please try again."



# Admin calendar route
@admin_bp.route('/admin_calendar', methods=['GET', 'POST'])
def admin_calendar():
    if request.method == 'POST':
        # Get the date and status from form
        date = request.form.get('date')
        status = request.form.get('status')

        # Update or insert into the MongoDB collection
        mongo.db.calendar.update_one(
            {'date': date},
            {'$set': {'status': status}},
            upsert=True
        )

        flash('Calendar updated successfully.')
        return redirect(url_for('admin.admin_calendar'))

    # Fetch current availability
    availability = list(mongo.db.calendar.find())

    # Format availability for the calendar
    events = []
    for entry in availability:
        events.append({
            'date': entry['date'],
            'status': entry['status']
        })

    return render_template('admin_calendar.html', events=events)


@home_bp.route('/check_availability', methods=['GET'])
def check_availability():
    date = request.args.get('date')

    # Query the `calendar` collection for busy dates
    busy_date = mongo.db.calendar.find_one({"date": date, "status": "busy"}) is not None

    # Return whether the date is busy
    return jsonify({"is_busy": busy_date})


@home_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            message_content = request.form.get('message')

            # Send an email to the admin
            admin_email = "your_email@example.com"
            msg = Message(subject=f"New Contact Form Submission from {name}",
                          sender=email,
                          recipients=[admin_email],
                          body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_content}")
            mail.send(msg)
            message = "Thank you for contacting us. We will get back to you soon!"
        except Exception as e:
            message = "There was an error sending your message. Please try again later."
            print(f"Error occurred: {e}")  # Print detailed error to the console
            return render_template('contact.html', message=message), 500

        return render_template('contact.html', message=message)

    return render_template('contact.html')

