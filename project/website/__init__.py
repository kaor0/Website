import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from os import path

db = SQLAlchemy()
DB_NAME = "database.db"

# Define upload folders
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/uploads')
GAMES_FOLDER = os.path.join(os.path.dirname(__file__), 'static/games')

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'docx'}

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'droduel23658'  # Consider using environment variable
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['GAMES_FOLDER'] = GAMES_FOLDER

    # Initialize SQLAlchemy with app
    db.init_app(app)

    # Create folders if they don't exist
    for folder in [UPLOAD_FOLDER, GAMES_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Import and register blueprints
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import models
    from .models import User, Note

    # Create database if it doesn't exist
    create_database(app)

    # Login manager setup
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app):
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Created Database!')