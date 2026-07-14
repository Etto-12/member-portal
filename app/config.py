import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    SQLALCHEMY_BINDS = {
        "applications": os.environ.get("APPLICATIONS_DATABASE_URL"),
        "id_assignment": os.environ.get("ID_ASSIGNMENT_DATABASE_URL"),
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False
