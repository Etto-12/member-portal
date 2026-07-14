from app import create_app
from app.extensions import db
from app.models.admin_user import AdminUser

app = create_app()
with app.app_context():
    admin = AdminUser(email="admin@local.test", is_superadmin=True)
    admin.set_password("upko1234")
    db.session.add(admin)
    db.session.commit()
    print("Admin created")
