import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

IS_PROD = os.environ.get("FLASK_ENV") == "production"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # ============ DATABASE ============
    database_url = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'lms.db')}"
    )
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
    }

    # ============ UPLOADS ============
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(BASE_DIR, "static", "uploads")
    )
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"mp4", "webm", "ogg", "mov", "pdf", "png", "jpg", "jpeg"}
    BLOCKED_EXTENSIONS = {
        "php", "py", "rb", "pl", "sh", "exe", "bat", "cmd",
        "jsp", "asp", "aspx", "cgi", "htm", "html", "svg", "js",
    }

    # ============ CLOUDINARY ============
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")
    USE_CLOUDINARY = bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY)

    # ============ OPENAI ============
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

    # ============ STRIPE ============
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")

    # ============ MAIL ============
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_USERNAME", "")

    # ============ SECURITY ============
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = IS_PROD

    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = IS_PROD
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Login lockout
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    # Rate limits (used in app.py)
    RATE_LOGIN = "5 per minute"
    RATE_REGISTER = "3 per hour"
    RATE_AI = "20 per hour"
    RATE_REVIEW = "10 per hour"
    RATE_DEFAULT = "500 per day;120 per hour"

    # ============ APP ============
    CATEGORIES = [
        "Programming", "Web Development", "Mobile Development",
        "Data Science", "AI & ML", "Design", "Business",
        "Marketing", "Mathematics", "Languages", "Other",
    ]
    LEVELS = ["Beginner", "Intermediate", "Advanced"]