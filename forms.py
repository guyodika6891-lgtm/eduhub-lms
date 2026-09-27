import re
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, TextAreaField, SelectField,
    IntegerField, FloatField, BooleanField, SubmitField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, Optional,
    NumberRange, ValidationError
)


# ============ CUSTOM VALIDATORS ============
def strong_password(form, field):
    pw = field.data or ""
    errors = []
    if len(pw) < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", pw):
        errors.append("one uppercase letter")
    if not re.search(r"[a-z]", pw):
        errors.append("one lowercase letter")
    if not re.search(r"\d", pw):
        errors.append("one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=]", pw):
        errors.append("one special character")
    if errors:
        raise ValidationError("Password must contain: " + ", ".join(errors))


def no_html(form, field):
    """Reject raw HTML tags to prevent stored XSS."""
    if field.data and re.search(r"<[^>]*>", field.data):
        raise ValidationError("HTML tags are not allowed.")


# ============ FORMS ============
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(3, 40)])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(2, 120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(5, 120)])
    password = PasswordField("Password", validators=[
        DataRequired(), Length(8, 100), strong_password,
    ])
    confirm = PasswordField("Confirm", validators=[DataRequired(), EqualTo("password")])
    role = SelectField("I am a",
                       choices=[("student", "Student"), ("teacher", "Teacher")],
                       validators=[DataRequired()])
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(1, 80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(1, 100)])
    submit = SubmitField("Login")


class CourseForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(3, 200)])
    description = TextAreaField("Description", validators=[Optional(), Length(0, 5000)])
    category = SelectField("Category", choices=[], validators=[DataRequired()])
    level = SelectField("Level", choices=[], validators=[DataRequired()])
    price = FloatField("Price (USD)", validators=[Optional(), NumberRange(min=0, max=10000)])
    cover_url = StringField("Cover image URL", validators=[Optional(), Length(0, 500)])
    published = BooleanField("Publish course")
    submit = SubmitField("Save Course")


class LessonForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(3, 200)])
    content = TextAreaField("Content", validators=[Optional(), Length(0, 10000)])
    video_url = StringField("Video URL", validators=[Optional(), Length(0, 500)])
    attachment_url = StringField("Attachment URL", validators=[Optional(), Length(0, 500)])
    duration_minutes = IntegerField("Duration (min)",
                                    validators=[Optional(), NumberRange(min=0, max=1000)])
    order_index = IntegerField("Order",
                               validators=[Optional(), NumberRange(min=0, max=1000)])
    submit = SubmitField("Save Lesson")


class ReviewForm(FlaskForm):
    rating = SelectField("Rating",
                         choices=[(str(i), f"{i} ⭐") for i in range(5, 0, -1)],
                         validators=[DataRequired()])
    comment = TextAreaField("Comment", validators=[Optional(), Length(0, 1000)])
    submit = SubmitField("Post Review")


class DiscussionForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(3, 200)])
    body = TextAreaField("Message", validators=[DataRequired(), Length(1, 3000)])
    submit = SubmitField("Post")


class ReplyForm(FlaskForm):
    body = TextAreaField("Reply", validators=[DataRequired(), Length(1, 2000)])
    submit = SubmitField("Reply")


class QuizForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(3, 200)])
    description = TextAreaField("Description", validators=[Optional(), Length(0, 1000)])
    submit = SubmitField("Create Quiz")


class QuestionForm(FlaskForm):
    body = TextAreaField("Question", validators=[DataRequired(), Length(1, 1000)])
    option_a = StringField("Option A", validators=[DataRequired(), Length(1, 300)])
    option_b = StringField("Option B", validators=[DataRequired(), Length(1, 300)])
    option_c = StringField("Option C", validators=[DataRequired(), Length(1, 300)])
    option_d = StringField("Option D", validators=[DataRequired(), Length(1, 300)])
    correct = SelectField("Correct",
                          choices=[("a", "A"), ("b", "B"), ("c", "C"), ("d", "D")],
                          validators=[DataRequired()])
    submit = SubmitField("Add Question")


class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[Optional(), Length(0, 120)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(0, 500)])
    avatar_url = StringField("Avatar URL", validators=[Optional(), Length(0, 500)])
    submit = SubmitField("Update Profile")