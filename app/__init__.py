from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///walletwizzard.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    from app import models

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.income import income_bp
    from app.routes.expense import expense_bp
    from app.routes.subscription import subscription_bp
    from app.routes.goal import goal_bp
    from app.routes.budget import budget_bp
    from app.routes.allocation import allocation_bp
    from app.routes.ai import ai_bp
    from app.routes.report import report_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(income_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(subscription_bp)
    app.register_blueprint(goal_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(allocation_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(report_bp)

    return app
