# models.py
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # NOVO: nome do arquivo do avatar (em static/avatars)
    avatar_filename = db.Column(db.String(255), nullable=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def avatar_url(self) -> str:
        """
        Retorna a URL do avatar ou um placeholder.
        """
        from flask import url_for

        if self.avatar_filename:
            return url_for("static", filename=f"avatars/{self.avatar_filename}")
        return url_for("static", filename="avatars/default.png")


class WatchProgress(db.Model):
    __tablename__ = "watch_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    relative_path = db.Column(db.String(500), nullable=False)
    serie_name = db.Column(db.String(255), nullable=False)
    episode_name = db.Column(db.String(255), nullable=False)
    last_watched = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship("User", backref=db.backref("watch_progress", lazy="dynamic"))

    __table_args__ = (
        db.UniqueConstraint("user_id", "relative_path", name="uq_progress_user_path"),
    )
