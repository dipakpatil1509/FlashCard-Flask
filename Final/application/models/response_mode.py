from datetime import datetime
from pytz import timezone
from application.database import db
from application.models.user_mode import User 
from application.models.deck import Card, Deck
import enum

Base = db.Model

class ReviewResponse(Base):
    __tablename__ = "reviewresponse"
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)

    avg_time = db.Column(db.Float(precision=2), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.now(timezone('Asia/Kolkata')))
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey(Deck.id), nullable=False)
    
    cards = db.relationship("ReviewCard", cascade="all,delete", backref="reviewcard", lazy='dynamic')

    def avg_time_count(self):
        return sum(card.time for card in self.cards)



class ReviewCard(Base):

    __tablename__ = "reviewcard"
    
    class Diffculty(enum.Enum):
        Easy = "1"
        Moderate = "2"
        Hard = "3"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    correct_option = db.Column(db.String, nullable = False)
    selected_option = db.Column(db.String, nullable = False)
    time = db.Column(db.Integer, nullable = False)
    correct = db.Column(db.Boolean)
    difficulty = db.Column(db.Enum(Diffculty), server_default="Moderate")
    completed_at = db.Column(db.DateTime, default=datetime.now(timezone('Asia/Kolkata')))

    card_id = db.Column(db.Integer, db.ForeignKey(Card.id), nullable=False)
    review_respose_id =  db.Column(db.Integer, db.ForeignKey(ReviewResponse.id, ondelete='CASCADE'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('card_id', 'review_respose_id', name='_review_respose_card_uc'),
    )



    