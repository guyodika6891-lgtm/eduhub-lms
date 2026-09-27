from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import func
from extensions import db


enrollments = db.Table(
    "enrollments",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), primary_key=True),
    db.Column("enrolled_at", db.DateTime, default=datetime.utcnow),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student")
    full_name = db.Column(db.String(120), default="")
    bio = db.Column(db.Text, default="")
    avatar_url = db.Column(db.String(500), default="")
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ===== SECURITY FIELDS =====
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)

    # ===== AI QUOTA =====
    ai_requests_today = db.Column(db.Integer, default=0)
    ai_reset_date = db.Column(db.Date, default=datetime.utcnow().date)

    courses = db.relationship("Course", backref="instructor", lazy="dynamic",
                              foreign_keys="Course.instructor_id")
    reviews = db.relationship("Review", backref="author", lazy="dynamic",
                              cascade="all, delete-orphan")
    submissions = db.relationship("QuizAttempt", backref="student",
                                  lazy="dynamic", cascade="all, delete-orphan")

    @property
    def is_admin(self): return self.role == "admin"
    @property
    def is_teacher(self): return self.role in ("admin", "teacher")
    @property
    def is_student(self): return self.role == "student"

    @property
    def is_locked(self):
        return self.locked_until and self.locked_until > datetime.utcnow()

    @property
    def enrolled_courses(self):
        return Course.query.join(enrollments, enrollments.c.course_id == Course.id)\
            .filter(enrollments.c.user_id == self.id).all()

    @property
    def total_points(self):
        return db.session.query(func.coalesce(func.sum(PointsLog.points), 0))\
            .filter(PointsLog.user_id == self.id).scalar()

    @property
    def badges(self):
        return [ub.badge for ub in UserBadge.query.filter_by(user_id=self.id).all()]


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(220), unique=True, index=True)
    description = db.Column(db.Text, default="")
    category = db.Column(db.String(40), default="Other", index=True)
    level = db.Column(db.String(20), default="Beginner")
    price = db.Column(db.Float, default=0.0)
    cover_url = db.Column(db.String(500), default="")
    published = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    lessons = db.relationship("Lesson", backref="course", lazy="dynamic",
                              cascade="all, delete-orphan",
                              order_by="Lesson.order_index")
    reviews = db.relationship("Review", backref="course", lazy="dynamic",
                              cascade="all, delete-orphan")
    discussions = db.relationship("Discussion", backref="course", lazy="dynamic",
                                  cascade="all, delete-orphan")

    @property
    def lesson_count(self): return self.lessons.count()

    @property
    def student_count(self):
        return db.session.query(enrollments).filter_by(course_id=self.id).count()

    @property
    def avg_rating(self):
        r = self.reviews.all()
        return round(sum(x.rating for x in r) / len(r), 1) if r else 0

    @property
    def total_duration(self):
        return sum(l.duration_minutes or 0 for l in self.lessons)


class Lesson(db.Model):
    __tablename__ = "lessons"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default="")
    video_url = db.Column(db.String(500), default="")
    attachment_url = db.Column(db.String(500), default="")
    duration_minutes = db.Column(db.Integer, default=0)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)

    completions = db.relationship("LessonCompletion", backref="lesson",
                                  lazy="dynamic", cascade="all, delete-orphan")


class LessonCompletion(db.Model):
    __tablename__ = "lesson_completions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"), nullable=False, index=True)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, default=5)
    comment = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)


class Discussion(db.Model):
    __tablename__ = "discussions"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)

    author = db.relationship("User")
    replies = db.relationship("Reply", backref="discussion", lazy="dynamic",
                              cascade="all, delete-orphan")


class Reply(db.Model):
    __tablename__ = "replies"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    discussion_id = db.Column(db.Integer, db.ForeignKey("discussions.id"), nullable=False)
    author = db.relationship("User")


class Quiz(db.Model):
    __tablename__ = "quizzes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)

    questions = db.relationship("Question", backref="quiz", lazy="dynamic",
                                cascade="all, delete-orphan")
    attempts = db.relationship("QuizAttempt", backref="quiz", lazy="dynamic",
                               cascade="all, delete-orphan")


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(300), nullable=False)
    option_b = db.Column(db.String(300), nullable=False)
    option_c = db.Column(db.String(300), nullable=False)
    option_d = db.Column(db.String(300), nullable=False)
    correct = db.Column(db.String(1), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)


class Certificate(db.Model):
    __tablename__ = "certificates"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, index=True)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    user = db.relationship("User")
    course = db.relationship("Course")


# ===== GAMIFICATION =====

class AIConversation(db.Model):
    __tablename__ = "ai_conversations"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class Badge(db.Model):
    __tablename__ = "badges"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    icon = db.Column(db.String(40), default="bi-award")
    description = db.Column(db.String(200), default="")


class UserBadge(db.Model):
    __tablename__ = "user_badges"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    badge = db.relationship("Badge")


class PointsLog(db.Model):
    __tablename__ = "points_log"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    points = db.Column(db.Integer, default=0)
    reason = db.Column(db.String(200), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    amount = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default="usd")
    stripe_session_id = db.Column(db.String(200), unique=True)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    course = db.relationship("Course")


# ===== SECURITY =====

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)