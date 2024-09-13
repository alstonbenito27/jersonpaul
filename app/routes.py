import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from bson.objectid import ObjectId  # Import ObjectId to handle MongoDB object IDs
from werkzeug.utils import secure_filename
from app import mongo

home_bp = Blueprint('home', __name__)
admin_bp = Blueprint('admin', __name__)

# Define the path to the image directories
GALLERY_FOLDER = 'app/static/uploads/gallery'  # Adjust this path to the actual folder location

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home page route
@home_bp.route('/')
def home():
    return render_template('home.html')


# Admin login page route
@admin_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = mongo.db.admin.find_one({"username": username})

        if admin and admin['password'] == password:  # Assuming plain text for testing
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid credentials')

    return render_template('admin_login.html')


# Admin dashboard route
@admin_bp.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')


# Admin services page route (handles both add and edit)
@admin_bp.route('/admin_services', methods=['GET', 'POST'])
def admin_services():
    if request.method == 'POST':
        service_id = request.form.get('service_id')
        name = request.form.get('name')
        description = request.form.get('description')

        if service_id:  # Update existing service
            mongo.db.services.update_one(
                {'_id': ObjectId(service_id)},
                {'$set': {'name': name, 'description': description}}
            )
            flash('Service updated successfully')
        else:  # Add new service
            mongo.db.services.insert_one({'name': name, 'description': description})
            flash('Service added successfully')

        return redirect(url_for('admin.admin_services'))

    services = mongo.db.services.find()
    service_id = request.args.get('service_id')
    service = mongo.db.services.find_one({'_id': ObjectId(service_id)}) if service_id else None

    return render_template('admin_services.html', services=services, service=service)


# Admin request page route
@admin_bp.route('/admin_request')
def admin_request():
    return render_template('admin_request.html')


# Admin gallery page route - Add, Edit and List images by category
@admin_bp.route('/admin_gallery', methods=['GET', 'POST'])
def admin_gallery():
    if request.method == 'POST':
        category = request.form.get('category')
        file = request.files.get('file')

        if category and file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(GALLERY_FOLDER, category, filename))
            flash(f'Image {filename} uploaded successfully!')
        else:
            flash('Invalid category or file!')

        return redirect(url_for('admin.admin_gallery'))

    # List images by category
    wedding_images = os.listdir(os.path.join(GALLERY_FOLDER, 'wedding'))
    corporate_images = os.listdir(os.path.join(GALLERY_FOLDER, 'corporate'))
    house_festivities_images = os.listdir(os.path.join(GALLERY_FOLDER, 'house_festivities'))

    return render_template(
        'admin_gallery.html',
        wedding_images=wedding_images,
        corporate_images=corporate_images,
        house_festivities_images=house_festivities_images
    )

# Route to serve the images
@admin_bp.route('/gallery/<category>/<filename>')
def gallery_image(category, filename):
    return send_from_directory(f'E:/Mini Project/THEPROJECTC/app/static/uploads/gallery/{category}', filename)


# Admin details page route
@admin_bp.route('/admin_details')
def admin_details():
    return render_template('admin_details.html')
