from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, migrate

# Models loaded for Flask-Migrate
from app.models.user import User
from app.models.hierarchy import HierarchyDocument
from app.models.membership_application import MembershipApplication
from app.models.id_assignment import IdAssignment

# Blueprints
from app.routes.auth import auth_bp
from app.routes.public import public_bp
from app.routes.admin import admin_bp
from app.routes.master import master_bp
from app.routes.hierarchy import hierarchy_bp
from app.routes.applications import applications_bp
from app.routes.id_assignment import id_assignment_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.config.update(
        SESSION_COOKIE_NAME="member_session",
    )

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(master_bp)
    app.register_blueprint(hierarchy_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(id_assignment_bp)

    return app


app = create_app()
