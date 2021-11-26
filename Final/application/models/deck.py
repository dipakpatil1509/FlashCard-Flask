from datetime import datetime
from pytz import timezone
import enum
from application.database import db
from application.models.user_mode import User

Base = db.Model

class Deck(Base):    
    
    
    class Type(enum.Enum):
        STUDENT = "1"
        TEACHER = "2"
        ALL = "3"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone('Asia/Kolkata')))
    created_by_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    created_for = db.Column(db.Enum(Type))
    public_status = db.Column(db.Boolean, default=True)
    
    cards = db.relationship("Card", cascade="all,delete", backref="deck", lazy='dynamic')

class Card(Base):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    front = db.Column(db.String, nullable = False)
    back = db.Column(db.String, nullable = False)
    options = db.Column(db.String, nullable = False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone('Asia/Kolkata')))
    created_by_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey(Deck.id, ondelete='CASCADE'), nullable=False)

    
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id'         : self.id,
            'options'    : self.options.split(','),
            'front'      : self.front,
            'back'       : self.back,
            'deck_id'    : self.deck_id,
            'created_by_id'  : self.created_by_id
        }

    def serialize_list(l):
        return [m.serialize() for m in l]
    