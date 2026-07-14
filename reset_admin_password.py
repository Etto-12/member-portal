from app import create_app
from app.extensions import db
from app.models.admin_user import AdminUser

app = create_app()

with app.app_context():
    admin = AdminUser.query.filter_by(email="admin@local.test").first()

    if admin:
        admin.set_password("admin123")
        db.session.commit()
        print("✅ Admin password reset to admin123")
    else:
        print("❌ Admin user not found")
