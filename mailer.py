import os
from flask import current_app, url_for
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

mail = Mail()


def init_mail(app):
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME")
    mail.init_app(app)


def generate_token(email):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps(email, salt="email-verify")


def verify_token(token, max_age=86400):
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return s.loads(token, salt="email-verify", max_age=max_age)
    except Exception:
        return None


def send_verification_email(user):
    if not current_app.config["MAIL_USERNAME"]:
        return  # mail not configured
    token = generate_token(user.email)
    link = url_for("verify_email", token=token, _external=True)
    msg = Message("Verify your EduHub account", recipients=[user.email])
    msg.html = f"""
      <h2>Welcome to EduHub! 🎓</h2>
      <p>Hi {user.full_name or user.username},</p>
      <p>Please confirm your email by clicking the button below:</p>
      <p><a href="{link}" style="background:#2563eb;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;">Verify Email</a></p>
      <p>Or copy this link: {link}</p>
    """
    try:
        mail.send(msg)
    except Exception as e:
        print("Mail error:", e)