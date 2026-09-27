import os
import uuid
from slugify import slugify
from werkzeug.utils import secure_filename
from flask import current_app, request


# ============ SLUGS ============
def make_slug(title):
    return slugify(title)[:200] or "course"


# ============ SAFE FILE UPLOADS ============
ALLOWED_MIMES = {
    # Video
    "video/mp4", "video/webm", "video/ogg", "video/quicktime",
    # Images
    "image/jpeg", "image/png", "image/webp", "image/gif",
    # Docs
    "application/pdf",
}


def _is_safe_upload(file, max_size_mb=500):
    """Verify file is genuinely safe before saving."""
    if not file or not file.filename:
        return False, "No file provided"

    # 1. Extension check
    ext = file.filename.rsplit(".", 1)[-1].lower()
    blocked = current_app.config.get("BLOCKED_EXTENSIONS", set())
    if ext in blocked:
        return False, f"Extension .{ext} not allowed"

    # 2. MIME type check (magic bytes)
    mime = None
    try:
        import magic
        header = file.read(2048)
        file.seek(0)
        mime = magic.from_buffer(header, mime=True)
    except Exception:
        # python-magic not available → fall back to extension whitelist
        allowed = current_app.config.get("ALLOWED_EXTENSIONS", set())
        if ext not in allowed:
            return False, f"Extension .{ext} not allowed"
        mime = "unknown"

    if mime != "unknown" and mime not in ALLOWED_MIMES:
        return False, f"File type {mime} not allowed"

    # 3. Size check
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > max_size_mb * 1024 * 1024:
        return False, f"File too large ({size // 1024 // 1024} MB, max {max_size_mb} MB)"

    return True, mime


def save_local_file(file):
    ok, msg = _is_safe_upload(file)
    if not ok:
        raise ValueError(msg)

    ext = file.filename.rsplit(".", 1)[-1].lower()
    name = secure_filename(f"{uuid.uuid4().hex}.{ext}")
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    file.save(path)
    return f"/uploads/{name}"


def upload_to_cloudinary(file, resource_type="auto"):
    import cloudinary, cloudinary.uploader
    ok, msg = _is_safe_upload(file)
    if not ok:
        raise ValueError(msg)
    cloudinary.config(
        cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=current_app.config["CLOUDINARY_API_KEY"],
        api_secret=current_app.config["CLOUDINARY_API_SECRET"],
        secure=True,
    )
    result = cloudinary.uploader.upload(file, resource_type=resource_type, folder="lms")
    return result["secure_url"]


# ============ AUDIT LOGGING ============
def audit(action, user_id=None, details=""):
    """Record a security-relevant event."""
    try:
        from models import AuditLog, db
        log = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string[:250] if request else None,
            details=str(details)[:500],
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"[audit error] {e}")


# ============ TEMPLATE HELPERS ============
def humanize(n):
    n = n or 0
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)


def time_ago(dt):
    from datetime import datetime
    if not dt: return ""
    s = int((datetime.utcnow() - dt).total_seconds())
    if s < 60: return "just now"
    if s < 3600: return f"{s//60}m ago"
    if s < 86400: return f"{s//3600}h ago"
    if s < 2592000: return f"{s//86400}d ago"
    if s < 31536000: return f"{s//2592000}mo ago"
    return f"{s//31536000}y ago"