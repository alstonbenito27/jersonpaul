from flask import Flask
from flask_pymongo import PyMongo
from flask_mail import Mail

# Global instances
mongo = PyMongo()
mail = Mail()  # Initialize mail object

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object('config.Config')

    # Initialize MongoDB
    mongo.init_app(app)

    # Initialize Mail
    mail.init_app(app)  # Initialize mail after app is created

    # Import and register blueprints
    from .routes import home_bp, admin_bp
    app.register_blueprint(home_bp)
    app.register_blueprint(admin_bp)

    return app