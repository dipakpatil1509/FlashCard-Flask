from datetime import datetime
import enum
from application.database import db
from flask_login import UserMixin

Base = db.Model


class User(Base, UserMixin):

    class Role(enum.Enum):
        STUDENT = "1"
        TEACHER = "2"
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(100))
    role = db.Column(db.Enum(Role), server_default="STUDENT")

    decks = db.relationship("Deck", backref="deck", lazy="dynamic")
    reviewResponses = db.relationship("ReviewResponse", backref="reviewresponse", lazy="dynamic")

    def review_response(self):
        try:
            return round(sum(review.score for review in self.reviewResponses)/self.reviewResponses.count(), 2)
        except:
            return 0.00