from sqlalchemy.dialects.postgresql import UUID
from app import db


class Move(db.Model):
    __tablename__ = "moves"
    __table_args__ = (db.UniqueConstraint('game_id', 'position'),)
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    move_no = db.Column(db.Integer)
    position = db.Column(db.Integer)

