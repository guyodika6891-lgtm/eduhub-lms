import os
import secrets
from datetime import datetime, timedelta, date
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, abort, send_from_directory, jsonify, send_file
)
from flask_login import login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, desc, func

from config import Config, IS_PROD
from extensions import db, login_manager, csrf
from models import (
    User, Course, Lesson, LessonCompletion, Review, Discussion,
    Reply, Quiz, Question, QuizAttempt, Certificate, enrollments,
    AIConversation, Payment, AuditLog
)
from forms import (
    RegisterForm, LoginForm, CourseForm, LessonForm,
    ReviewForm, DiscussionForm, ReplyForm, QuizForm,
    QuestionForm, ProfileForm
)
from decorators import teacher_required, admin_required
from utils import make_slug, humanize, time_ago, audit, save_local_file
from gamification import award_points, leaderboard
from ai_assistant import ask_ai
from certificate_pdf import generate_certificate_pdf
from mailer import init_mail, send_verification_email, verify_token
from payments import create_checkout_session

socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["500 per day", "120 per hour"],
    storage_uri="memory://",  # upgrade to Redis in production for multi-worker
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    init_mail(app)
    socketio.init_app(app)
    limiter.init_app(app)

    # ============ SECURITY HEADERS (Talisman) ============
    csp = {
        'default-src': ["'self'"],
        'script-src': [
            "'self'", "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://cdn.socket.io",
            "https://cdnjs.cloudflare.com",
        ],
        'style-src': [
            "'self'", "'unsafe-inline'",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
            "https://fonts.googleapis.com",
        ],
        'font-src': [
            "'self'",
            "https://fonts.gstatic.com",
            "https://cdn.jsdelivr.net",
            "https://cdnjs.cloudflare.com",
        ],
        'img-src': ["'self'", "data:", "https:"],
        'connect-src': ["'self'", "wss:", "https:"],
        'frame-src': ["'self'", "https://www.youtube.com"],
        'object-src': ["'none'"],
        'base-uri': ["'self'"],
    }
    Talisman(
        app,
        content_security_policy=csp,
        force_https=IS_PROD,
        session_cookie_secure=IS_PROD,
        frame_options="SAMEORIGIN",
        referrer_policy="strict-origin-when-cross-origin",
        strict_transport_security=IS_PROD,
        strict_transport_security_max_age=31536000,
        content_security_policy_nonce_in=['script-src'],
    )

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with app.app_context():
        db.create_all()

    app.jinja_env.filters["humanize"] = humanize
    app.jinja_env.filters["time_ago"] = time_ago

    register_routes(app)
    register_socket_events()
    register_errors(app)
    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def register_errors(app):
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def nf(e):
        return render_template("404.html"), 404

    @app.errorhandler(429)
    def ratelimit(e):
        return render_template("429.html", error=str(e)), 429

    @app.errorhandler(500)
    def se(e):
        db.session.rollback()
        try:
            audit("SERVER_ERROR", details=str(e)[:400])
        except Exception:
            pass
        return render_template("500.html"), 500


def register_socket_events():
    @socketio.on("connect")
    def on_connect():
        if current_user.is_authenticated:
            join_room(f"user_{current_user.id}")

    @socketio.on("join_course_chat")
    def join_course(data):
        if current_user.is_authenticated:
            room = f"course_{data.get('course_id')}"
            join_room(room)
            emit("system", {"msg": f"{current_user.username} joined"}, to=room)

    @socketio.on("chat_message")
    def chat_message(data):
        if current_user.is_authenticated:
            msg = str(data.get("msg", ""))[:500]
            emit("chat_message", {
                "user": current_user.username,
                "msg": msg,
                "ts": datetime.utcnow().strftime("%H:%M"),
            }, to=f"course_{data.get('course_id')}")


def notify_user(user_id, message):
    socketio.emit("notification", {"msg": message}, to=f"user_{user_id}")


def register_routes(app):

    # ============ HOME ============
    @app.route("/")
    def index():
        q = request.args.get("q", "").strip()[:100]
        cat = request.args.get("category", "").strip()[:50]
        level = request.args.get("level", "").strip()[:20]

        query = Course.query.filter_by(published=True)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(Course.title.ilike(like), Course.description.ilike(like)))
        if cat: query = query.filter(Course.category == cat)
        if level: query = query.filter(Course.level == level)

        courses = query.order_by(Course.created_at.desc()).limit(60).all()
        featured = Course.query.filter_by(published=True)\
            .order_by(Course.created_at.desc()).limit(3).all()
        return render_template("index.html", courses=courses, featured=featured,
                               q=q, category=cat, level=level,
                               categories=Config.CATEGORIES, levels=Config.LEVELS)

    # ============ AUTH ============
    @app.route("/register", methods=["GET", "POST"])
    @limiter.limit(Config.RATE_REGISTER)
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        form = RegisterForm()
        if form.validate_on_submit():
            username = form.username.data.strip()
            email = form.email.data.strip().lower()
            if User.query.filter((User.username == username) | (User.email == email)).first():
                flash("Username or email already taken.", "danger")
            else:
                role = form.role.data
                if User.query.count() == 0:
                    role = "admin"
                user = User(
                    username=username, email=email,
                    full_name=form.full_name.data.strip(), role=role,
                    password=generate_password_hash(form.password.data),
                )
                db.session.add(user)
                db.session.commit()
                audit("REGISTER", user.id, details=f"role={role}")
                try:
                    send_verification_email(user)
                except Exception as e:
                    print("verify mail failed:", e)
                login_user(user)
                flash("Welcome to EduHub!", "success")
                return redirect(url_for("dashboard"))
        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit(Config.RATE_LOGIN)
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data.strip()
            user = User.query.filter_by(username=username).first()

            if user and user.is_locked:
                remaining = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
                audit("LOGIN_LOCKED", details=f"user={username}")
                flash(f"Account locked. Try again in {remaining} min.", "danger")
                return render_template("login.html", form=form)

            if user and check_password_hash(user.password, form.password.data):
                user.failed_login_attempts = 0
                user.locked_until = None
                user.last_login_at = datetime.utcnow()
                user.last_login_ip = request.remote_addr
                db.session.commit()
                login_user(user, remember=True)
                audit("LOGIN_SUCCESS", user.id)
                flash(f"Welcome back, {user.username}!", "success")
                return redirect(request.args.get("next") or url_for("dashboard"))

            # Failed login
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= Config.MAX_LOGIN_ATTEMPTS:
                    user.locked_until = datetime.utcnow() + timedelta(
                        minutes=Config.LOCKOUT_DURATION_MINUTES)
                    audit("LOGIN_LOCKOUT", user.id, f"after {user.failed_login_attempts} attempts")
                    flash(f"Too many failed attempts. Locked for {Config.LOCKOUT_DURATION_MINUTES} minutes.", "danger")
                else:
                    audit("LOGIN_FAILED", user.id)
                    flash("Invalid credentials.", "danger")
                db.session.commit()
            else:
                audit("LOGIN_FAILED", details=f"unknown user={username}")
                flash("Invalid credentials.", "danger")
        return render_template("login.html", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        audit("LOGOUT", current_user.id)
        logout_user()
        flash("Logged out.", "info")
        return redirect(url_for("index"))

    @app.route("/verify/<token>")
    def verify_email(token):
        email = verify_token(token)
        if not email:
            flash("Invalid or expired link.", "danger")
            return redirect(url_for("login"))
        user = User.query.filter_by(email=email).first()
        if user:
            user.email_verified = True
            db.session.commit()
            audit("EMAIL_VERIFIED", user.id)
            flash("✅ Email verified!", "success")
        return redirect(url_for("login"))

    # ============ DASHBOARDS ============
    @app.route("/dashboard")
    @login_required
    def dashboard():
        if current_user.is_admin: return redirect(url_for("admin_dashboard"))
        if current_user.is_teacher: return redirect(url_for("teacher_dashboard"))
        return redirect(url_for("student_dashboard"))

    @app.route("/dashboard/student")
    @login_required
    def student_dashboard():
        enrolled = current_user.enrolled_courses
        completed = LessonCompletion.query.filter_by(user_id=current_user.id).count()
        attempts = QuizAttempt.query.filter_by(user_id=current_user.id)\
            .order_by(desc(QuizAttempt.attempted_at)).limit(5).all()
        certs = Certificate.query.filter_by(user_id=current_user.id).all()
        return render_template("dashboard_student.html",
                               enrolled=enrolled, completed_lessons=completed,
                               attempts=attempts, certificates=certs)

    @app.route("/dashboard/teacher")
    @login_required
    @teacher_required
    def teacher_dashboard():
        courses = current_user.courses.all()
        total_students = sum(c.student_count for c in courses)
        total_lessons = sum(c.lesson_count for c in courses)
        return render_template("dashboard_teacher.html", courses=courses,
                               total_students=total_students, total_lessons=total_lessons)

    @app.route("/dashboard/teacher/analytics")
    @login_required
    @teacher_required
    def teacher_analytics():
        courses = current_user.courses.all()
        course_ids = [c.id for c in courses]
        days, counts = [], []
        for i in range(29, -1, -1):
            day = datetime.utcnow().date() - timedelta(days=i)
            days.append(day.strftime("%b %d"))
            n = db.session.query(enrollments).filter(
                enrollments.c.course_id.in_(course_ids),
                func.date(enrollments.c.enrolled_at) == day
            ).count() if course_ids else 0
            counts.append(n)

        top_courses = sorted(courses, key=lambda c: c.student_count, reverse=True)[:5]
        quiz_attempts = QuizAttempt.query.join(Quiz).filter(
            Quiz.course_id.in_(course_ids)
        ).count() if course_ids else 0
        return render_template("teacher_analytics.html",
                               days=days, counts=counts,
                               top_courses=top_courses, quiz_attempts=quiz_attempts)

    @app.route("/dashboard/admin")
    @login_required
    @admin_required
    def admin_dashboard():
        stats = {
            "users": User.query.count(),
            "teachers": User.query.filter_by(role="teacher").count(),
            "students": User.query.filter_by(role="student").count(),
            "courses": Course.query.count(),
            "lessons": Lesson.query.count(),
            "enrollments": db.session.query(enrollments).count(),
        }
        users = User.query.order_by(desc(User.created_at)).limit(10).all()
        courses = Course.query.order_by(desc(Course.created_at)).limit(10).all()
        recent_audit = AuditLog.query.order_by(desc(AuditLog.created_at)).limit(20).all()
        return render_template("dashboard_admin.html",
                               stats=stats, users=users,
                               courses=courses, audit_logs=recent_audit)

    @app.route("/leaderboard")
    @login_required
    def leaderboard_view():
        return render_template("leaderboard.html", rows=leaderboard(50))

    # ============ COURSES ============
    @app.route("/courses")
    def course_list():
        q = request.args.get("q", "").strip()[:100]
        cat = request.args.get("category", "").strip()[:50]
        level = request.args.get("level", "").strip()[:20]

        query = Course.query.filter_by(published=True)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(Course.title.ilike(like), Course.description.ilike(like)))
        if cat: query = query.filter(Course.category == cat)
        if level: query = query.filter(Course.level == level)

        courses = query.order_by(Course.created_at.desc()).all()
        return render_template("course_list.html", courses=courses, q=q,
                               category=cat, level=level,
                               categories=Config.CATEGORIES, levels=Config.LEVELS)

    @app.route("/course/<slug>")
    def course_detail(slug):
        slug = slug[:220]
        course = Course.query.filter_by(slug=slug).first_or_404()
        if not course.published and not (
            current_user.is_authenticated and
            (current_user.id == course.instructor_id or current_user.is_admin)
        ):
            abort(404)

        enrolled = False
        if current_user.is_authenticated:
            enrolled = db.session.query(enrollments).filter_by(
                user_id=current_user.id, course_id=course.id).first() is not None

        reviews = course.reviews.order_by(desc(Review.created_at)).all()
        discussions = course.discussions.order_by(desc(Discussion.created_at)).limit(5).all()
        quizzes = Quiz.query.filter_by(course_id=course.id).all()
        return render_template("course_detail.html",
                               course=course, enrolled=enrolled, reviews=reviews,
                               discussions=discussions, quizzes=quizzes,
                               review_form=ReviewForm(), discussion_form=DiscussionForm())

    @app.route("/course/new", methods=["GET", "POST"])
    @login_required
    @teacher_required
    def course_create():
        form = CourseForm()
        form.category.choices = [(c, c) for c in Config.CATEGORIES]
        form.level.choices = [(l, l) for l in Config.LEVELS]
        if form.validate_on_submit():
            base = make_slug(form.title.data)
            slug, i = base, 1
            while Course.query.filter_by(slug=slug).first():
                slug = f"{base}-{i}"; i += 1
            course = Course(
                title=form.title.data.strip(), slug=slug,
                description=form.description.data or "",
                category=form.category.data, level=form.level.data,
                price=form.price.data or 0.0,
                cover_url=form.cover_url.data or "",
                published=form.published.data,
                instructor_id=current_user.id,
            )
            db.session.add(course)
            db.session.commit()
            audit("COURSE_CREATE", current_user.id, f"slug={slug}")
            flash("Course created!", "success")
            return redirect(url_for("course_detail", slug=course.slug))
        return render_template("course_form.html", form=form, course=None)

    @app.route("/course/<slug>/edit", methods=["GET", "POST"])
    @login_required
    @teacher_required
    def course_edit(slug):
        course = Course.query.filter_by(slug=slug).first_or_404()
        if course.instructor_id != current_user.id and not current_user.is_admin:
            abort(403)
        form = CourseForm(obj=course)
        form.category.choices = [(c, c) for c in Config.CATEGORIES]
        form.level.choices = [(l, l) for l in Config.LEVELS]
        if form.validate_on_submit():
            course.title = form.title.data.strip()
            course.description = form.description.data or ""
            course.category = form.category.data
            course.level = form.level.data
            course.price = form.price.data or 0.0
            course.cover_url = form.cover_url.data or ""
            course.published = form.published.data
            db.session.commit()
            audit("COURSE_EDIT", current_user.id, f"slug={slug}")
            flash("Course updated.", "success")
            return redirect(url_for("course_detail", slug=course.slug))
        return render_template("course_form.html", form=form, course=course)

    @app.route("/course/<slug>/delete", methods=["POST"])
    @login_required
    @teacher_required
    def course_delete(slug):
        course = Course.query.filter_by(slug=slug).first_or_404()
        if course.instructor_id != current_user.id and not current_user.is_admin:
            abort(403)
        db.session.delete(course)
        db.session.commit()
        audit("COURSE_DELETE", current_user.id, f"slug={slug}")
        flash("Course deleted.", "info")
        return redirect(url_for("teacher_dashboard"))

    # ============ ENROLLMENT ============
    @app.route("/course/<slug>/enroll", methods=["POST"])
    @login_required
    def enroll(slug):
        course = Course.query.filter_by(slug=slug).first_or_404()
        exists = db.session.query(enrollments).filter_by(
            user_id=current_user.id, course_id=course.id).first()
        if not exists:
            db.session.execute(enrollments.insert().values(
                user_id=current_user.id, course_id=course.id))
            db.session.commit()
            audit("ENROLL", current_user.id, f"course={course.slug}")
            notify_user(course.instructor_id, f"🎓 New student: {current_user.username}")
            flash(f"Enrolled in '{course.title}'!", "success")
        return redirect(url_for("course_detail", slug=course.slug))

    @app.route("/course/<slug>/unenroll", methods=["POST"])
    @login_required
    def unenroll(slug):
        course = Course.query.filter_by(slug=slug).first_or_404()
        db.session.execute(enrollments.delete().where(
            (enrollments.c.user_id == current_user.id) &
            (enrollments.c.course_id == course.id)))
        db.session.commit()
        audit("UNENROLL", current_user.id, f"course={course.slug}")
        flash("Unenrolled.", "info")
        return redirect(url_for("course_detail", slug=course.slug))

    @app.route("/my-courses")
    @login_required
    def my_courses():
        return render_template("my_courses.html", courses=current_user.enrolled_courses)

    # ============ PAYMENTS ============
    @app.route("/course/<slug>/buy", methods=["POST"])
    @login_required
    @limiter.limit("10 per hour")
    def course_buy(slug):
        course = Course.query.filter_by(slug=slug).first_or_404()
        if course.price <= 0:
            return redirect(url_for("enroll", slug=slug))
        if not app.config["STRIPE_SECRET_KEY"]:
            flash("Payments not configured. Enrolling for free (demo mode).", "warning")
            return redirect(url_for("enroll", slug=slug))
        session = create_checkout_session(
            course, current_user,
            success_url=url_for("payment_success", slug=slug, _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for("course_detail", slug=slug, _external=True),
        )
        db.session.add(Payment(
            user_id=current_user.id, course_id=course.id,
            amount=course.price, stripe_session_id=session.id))
        db.session.commit()
        audit("PAYMENT_INIT", current_user.id, f"course={slug}, amount={course.price}")
        return redirect(session.url, code=303)

    @app.route("/payment/success/<slug>")
    @login_required
    def payment_success(slug):
        course = Course.query.filter_by(slug=slug).first_or_404()
        payment = Payment.query.filter_by(
            user_id=current_user.id, course_id=course.id, status="pending"
        ).order_by(desc(Payment.created_at)).first()
        if payment:
            payment.status = "paid"
            exists = db.session.query(enrollments).filter_by(
                user_id=current_user.id, course_id=course.id).first()
            if not exists:
                db.session.execute(enrollments.insert().values(
                    user_id=current_user.id, course_id=course.id))
            db.session.commit()
            audit("PAYMENT_SUCCESS", current_user.id, f"course={slug}")
            flash("✅ Payment successful! Enrolled.", "success")
        return redirect(url_for("course_detail", slug=course.slug))

    # ============ LESSONS ============
    @app.route("/course/<slug>/lesson/new", methods=["GET", "POST"])
    @login_required
    @teacher_required
    def lesson_create(slug):
        course = Course.query.filter_by(slug=slug).first_or_404()
        if course.instructor_id != current_user.id and not current_user.is_admin:
            abort(403)
        form = LessonForm()
        if form.validate_on_submit():
            db.session.add(Lesson(
                title=form.title.data.strip(), content=form.content.data or "",
                video_url=form.video_url.data or "",
                attachment_url=form.attachment_url.data or "",
                duration_minutes=form.duration_minutes.data or 0,
                order_index=form.order_index.data or (course.lesson_count + 1),
                course_id=course.id))
            db.session.commit()
            audit("LESSON_CREATE", current_user.id, f"course={slug}")
            flash("Lesson added.", "success")
            return redirect(url_for("course_detail", slug=course.slug))
        return render_template("lesson_form.html", form=form, course=course, lesson=None)

    @app.route("/lesson/<int:lesson_id>/edit", methods=["GET", "POST"])
    @login_required
    @teacher_required
    def lesson_edit(lesson_id):
        lesson = Lesson.query.get_or_404(lesson_id)
        course = lesson.course
        if course.instructor_id != current_user.id and not current_user.is_admin:
            abort(403)
        form = LessonForm(obj=lesson)
        if form.validate_on_submit():
            lesson.title = form.title.data.strip()
            lesson.content = form.content.data or ""
            lesson.video_url = form.video_url.data or ""
            lesson.attachment_url = form.attachment_url.data or ""
            lesson.duration_minutes = form.duration_minutes.data or 0
            lesson.order_index = form.order_index.data or lesson.order_index
            db.session.commit()
            flash("Lesson updated.", "success")
            return redirect(url_for("course_detail", slug=course.slug))
        return render_template("lesson_form.html", form=form, course=course, lesson=lesson)

    @app.route("/lesson/<int:lesson_id>/delete", methods=["POST"])
    @login_required
    @teacher_required
    def lesson_delete(lesson_id):
        lesson = Lesson.query.get_or_404(lesson_id)
        course = lesson.course
        if course.instructor_id != current_user.id and not current_user.is_admin:
            abort(403)
        db.session.delete(lesson)
        db.session.commit()
        flash("Lesson deleted.", "info")
        return redirect(url_for("course_detail", slug=course.slug))

    @app.route("/lesson/<int:lesson_id>")
    @login_required
    def lesson_view(lesson_id):
        lesson = Lesson.query.get_or_404(lesson_id)
        course = lesson.course
        enrolled = db.session.query(enrollments).filter_by(
            user_id=current_user.id, course_id=course.id).first() is not None
        if not enrolled and current_user.id != course.instructor_id and not current_user.is_admin:
            flash("Enroll to access this lesson.", "warning")
            return redirect(url_for("course_detail", slug=course.slug))
        completed = LessonCompletion.query.filter_by(
            user_id=current_user.id, lesson_id=lesson.id).first() is not None
        return render_template("lesson_view.html", lesson=lesson, course=course, completed=completed)

    @app.route("/lesson/<int:lesson_id>/complete", methods=["POST"])
    @login_required
    def lesson_complete(lesson_id):
        lesson = Lesson.query.get_or_404(lesson_id)
        exists = LessonCompletion.query.filter_by(
            user_id=current_user.id, lesson_id=lesson.id).first()
        if not exists:
            db.session.add(LessonCompletion(user_id=current_user.id, lesson_id=lesson.id))
            db.session.commit()
            award_points(current_user, 10, "Lesson completed")

        course = lesson.course
        total = course.lesson_count
        done = LessonCompletion.query.filter_by(user_id=current_user.id)\
            .join(Lesson, Lesson.id == LessonCompletion.lesson_id)\
            .filter(Lesson.course_id == course.id).count()

        if total > 0 and done >= total:
            cert = Certificate.query.filter_by(
                user_id=current_user.id, course_id=course.id).first()
            if not cert:
                cert = Certificate(code=secrets.token_urlsafe(12),
                                   user_id=current_user.id, course_id=course.id)
                db.session.add(cert)
                db.session.commit()
                award_points(current_user, 50, "Course completed")
                audit("CERTIFICATE_ISSUED", current_user.id, f"course={course.slug}")
                flash("🎉 Course completed! Certificate issued.", "success")
                return redirect(url_for("certificate_view", code=cert.code))
        flash("Lesson marked complete (+10 pts).", "success")
        return redirect(url_for("lesson_view", lesson_id=lesson.id))

    # ============ REVIEWS ============
    @app.route("/course/<slug>/review", methods=["POST"])
    @login_required
    @limiter.limit(Config.RATE_REVIEW)
    def post_review(slug):
        course = Course.query.filter_by(slug=slug).first_or_404()
        form = ReviewForm()
        if form.validate_on_submit():
            existing = Review.query.filter_by(
                user_id=current_user.id, course_id=course.id).first()
            if existing:
                existing.rating = int(form.rating.data)
                existing.comment = form.comment.data or ""
            else:
                db.session.add(Review(
                    rating=int(form.rating.data), comment=form.comment.data or "",
                    user_id=current_user.id, course_id=course.id))
            db.session.commit()
            flash("Review posted.", "success")
        return redirect(url_for("course_detail", slug=course.slug))

    # ============ DISCUSSIONS ============
    @app.route("/course/<slug>/discussion/new", methods=["POST"])
    @login_required
    @limiter.limit("10 per hour")
    def post_discussion(slug):
        course = Course.query.filter_by(slug=slug).first_or_404()
        form = DiscussionForm()
        if form.validate_on_submit():
            db.session.add(Discussion(
                title=form.title.data.strip(), body=form.body.data.strip(),
                user_id=current_user.id, course_id=course.id))
            db.session.commit()
            flash("Discussion posted.", "success")
        return redirect(url_for("course_detail", slug=course.slug))

    @app.route("/discussion/<int:discussion_id>", methods=["GET", "POST"])
    @login_required
    def discussion_view(discussion_id):
        d = Discussion.query.get_or_404(discussion_id)
        form = ReplyForm()
        if form.validate_on_submit():
            db.session.add(Reply(body=form.body.data.strip(),
                                 user_id=current_user.id, discussion_id=d.id))
            db.session.commit()
            flash("Reply posted.", "success")
            return redirect(url_for("discussion_view", discussion_id=d.id))
        return render_template("discussion_view.html", discussion=d, form=form)

    # ============ QUIZZES ============
    @app.route("/course/<slug>/quiz/new", methods=["GET", "POST"])
    @login_required
    @teacher_required
    def quiz_create(slug):
        course = Course.query.filter_by(slug=slug).first_or_404()
        if course.instructor_id != current_user.id and not current_user.is_admin:
            abort(403)
        form = QuizForm()
        if form.validate_on_submit():
            quiz = Quiz(title=form.title.data.strip(),
                        description=form.description.data or "",
                        course_id=course.id)
            db.session.add(quiz)
            db.session.commit()
            flash("Quiz created. Add questions below.", "success")
            return redirect(url_for("quiz_edit", quiz_id=quiz.id))
        return render_template("quiz_form.html", form=form, course=course)

    @app.route("/quiz/<int:quiz_id>/edit", methods=["GET", "POST"])
    @login_required
    @teacher_required
    def quiz_edit(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        course = quiz.course
        if course.instructor_id != current_user.id and not current_user.is_admin:
            abort(403)
        form = QuestionForm()
        if form.validate_on_submit():
            db.session.add(Question(
                body=form.body.data.strip(),
                option_a=form.option_a.data.strip(),
                option_b=form.option_b.data.strip(),
                option_c=form.option_c.data.strip(),
                option_d=form.option_d.data.strip(),
                correct=form.correct.data, quiz_id=quiz.id))
            db.session.commit()
            flash("Question added.", "success")
            return redirect(url_for("quiz_edit", quiz_id=quiz.id))
        return render_template("quiz_form.html", form=form, quiz=quiz,
                               course=course, questions=quiz.questions.all())

    @app.route("/quiz/<int:quiz_id>/take", methods=["GET", "POST"])
    @login_required
    @limiter.limit("30 per hour")
    def quiz_take(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        questions = quiz.questions.all()
        if not questions:
            flash("No questions yet.", "warning")
            return redirect(url_for("course_detail", slug=quiz.course.slug))
        if request.method == "POST":
            score = 0
            for q in questions:
                if (request.form.get(f"q_{q.id}") or "").lower() == q.correct:
                    score += 1
            attempt = QuizAttempt(score=score, total=len(questions),
                                  user_id=current_user.id, quiz_id=quiz.id)
            db.session.add(attempt)
            db.session.commit()
            award_points(current_user, score * 5, f"Quiz: {quiz.title}")
            return render_template("quiz_result.html", quiz=quiz, attempt=attempt)
        return render_template("quiz.html", quiz=quiz, questions=questions)

    # ============ CERTIFICATES ============
    @app.route("/certificate/<code>")
    @login_required
    def certificate_view(code):
        cert = Certificate.query.filter_by(code=code[:40]).first_or_404()
        if cert.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        return render_template("certificate.html", cert=cert)

    @app.route("/certificate/<code>/download")
    @login_required
    def certificate_download(code):
        cert = Certificate.query.filter_by(code=code[:40]).first_or_404()
        if cert.user_id != current_user.id and not current_user.is_admin:
            abort(403)
        tmp_dir = os.path.join(app.config["UPLOAD_FOLDER"], "certificates")
        os.makedirs(tmp_dir, exist_ok=True)
        path = os.path.join(tmp_dir, f"{cert.code}.pdf")
        generate_certificate_pdf(cert, cert.user, cert.course, path)
        return send_file(path, as_attachment=True,
                         download_name=f"certificate-{cert.course.slug}.pdf")

    # ============ AI ============
    @app.route("/ai/ask", methods=["POST"])
    @login_required
    @limiter.limit(Config.RATE_AI)
    def ai_ask():
        data = request.get_json() or {}
        question = str(data.get("question", "")).strip()[:500]
        course_id = data.get("course_id")

        if not question:
            return jsonify({"error": "No question"}), 400

        # Daily quota
        today = date.today()
        if current_user.ai_reset_date != today:
            current_user.ai_requests_today = 0
            current_user.ai_reset_date = today
            db.session.commit()

        if (current_user.ai_requests_today or 0) >= 50:
            return jsonify({"answer": "Daily AI limit reached. Try tomorrow."}), 429

        context = ""
        if course_id:
            course = Course.query.get(course_id)
            if course:
                context = f"Course: {course.title}\n{course.description}\n"
                context += "\n".join(f"- {l.title}: {l.content[:300]}"
                                     for l in course.lessons)

        history_qs = AIConversation.query.filter_by(user_id=current_user.id)\
            .order_by(desc(AIConversation.created_at)).limit(5).all()
        history = []
        for h in reversed(history_qs):
            history.append({"role": "user", "content": h.question})
            history.append({"role": "assistant", "content": h.answer})

        answer = ask_ai(question, context, history)
        db.session.add(AIConversation(user_id=current_user.id, course_id=course_id,
                                      question=question, answer=answer))
        current_user.ai_requests_today = (current_user.ai_requests_today or 0) + 1
        db.session.commit()
        return jsonify({"answer": answer})

    # ============ PROFILE ============
    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        form = ProfileForm(obj=current_user)
        if form.validate_on_submit():
            current_user.full_name = form.full_name.data or ""
            current_user.bio = form.bio.data or ""
            current_user.avatar_url = form.avatar_url.data or ""
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("profile"))
        return render_template("profile.html", form=form)

    # ============ FILES ============
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        # Prevent path traversal
        filename = os.path.basename(filename)
        response = send_from_directory(app.config["UPLOAD_FOLDER"], filename)
        response.headers["Content-Disposition"] = "inline"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.route("/healthz")
    def healthz():
        return {"status": "ok", "time": datetime.utcnow().isoformat()}


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = not IS_PROD
    socketio.run(app, host="0.0.0.0", port=port, debug=debug_mode,
                 allow_unsafe_werkzeug=True)