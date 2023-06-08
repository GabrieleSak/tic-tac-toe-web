from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from app import db
from .game import Game
from sqlalchemy import and_


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String())
    moves = db.relationship("Move")

    def is_part_of_game(self):
        if (db.session.query(Game).filter(and_(Game.user_id_x == self.id, Game.result == None)).first() is not None
                or
                db.session.query(Game).filter(
                    and_(Game.user_id_o == self.id, Game.result == None)).first() is not None):
            return True
        return False

    def get_game_id(self):
        if db.session.query(Game).filter(and_(Game.user_id_x == self.id, Game.result == None)).first() is not None:
            game_id = [r.id for r in
                       db.session.query(Game).filter(and_(Game.user_id_x == self.id, Game.result == None))]
        else:
            game_id = [r.id for r in
                       db.session.query(Game).filter(and_(Game.user_id_o == self.id, Game.result == None))]
        return game_id[0]
