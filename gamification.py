from models import db, PointsLog, Badge, UserBadge


def award_points(user, points, reason):
    db.session.add(PointsLog(user_id=user.id, points=points, reason=reason))
    db.session.commit()
    check_badges(user)


def check_badges(user):
    from models import LessonCompletion, Certificate

    rules = [
        ("First Steps", "bi-flag", "Complete your first lesson",
         LessonCompletion.query.filter_by(user_id=user.id).count() >= 1),
        ("Learner", "bi-book", "Complete 10 lessons",
         LessonCompletion.query.filter_by(user_id=user.id).count() >= 10),
        ("Scholar", "bi-mortarboard", "Complete 50 lessons",
         LessonCompletion.query.filter_by(user_id=user.id).count() >= 50),
        ("Graduate", "bi-trophy", "Earn your first certificate",
         Certificate.query.filter_by(user_id=user.id).count() >= 1),
        ("Master", "bi-award-fill", "Earn 5 certificates",
         Certificate.query.filter_by(user_id=user.id).count() >= 5),
    ]

    for name, icon, desc, condition in rules:
        if not condition:
            continue
        badge = Badge.query.filter_by(name=name).first()
        if not badge:
            badge = Badge(name=name, icon=icon, description=desc)
            db.session.add(badge)
            db.session.commit()
        existing = UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first()
        if not existing:
            db.session.add(UserBadge(user_id=user.id, badge_id=badge.id))
            db.session.commit()


def leaderboard(limit=20):
    from models import User
    from sqlalchemy import func
    rows = (
        db.session.query(User, func.coalesce(func.sum(PointsLog.points), 0).label("pts"))
        .outerjoin(PointsLog, PointsLog.user_id == User.id)
        .filter(User.role == "student")
        .group_by(User.id)
        .order_by(func.coalesce(func.sum(PointsLog.points), 0).desc())
        .limit(limit).all()
    )
    return rows