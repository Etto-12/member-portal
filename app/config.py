import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    # Main memberdb connection protection
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    SQLALCHEMY_BINDS = {
        "applications": {
            "url": os.environ.get("APPLICATIONS_DATABASE_URL"),
            "pool_pre_ping": True,
            "pool_recycle": 1800,
        },

        "id_assignment": {
            "url": os.environ.get("ID_ASSIGNMENT_DATABASE_URL"),
            "pool_pre_ping": True,
            "pool_recycle": 1800,
        },
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False
