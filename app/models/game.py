from sqlalchemy.dialects.postgresql import UUID
from app import db
import random
from .move import Move


class Game(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    user_id_x = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    user_id_o = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    moves = db.relationship("Move")
    first_player = db.Column(db.String())
    result = db.Column(db.String())

    @classmethod
    def game_waiting_second_player(cls):
        game_x = db.session.query(Game).filter(Game.user_id_x == None).first()
        game_o = db.session.query(Game).filter(Game.user_id_o == None).first()
        if game_x is not None:
            return game_x.id, "user_id_x"
        elif game_o is not None:
            return game_o.id, "user_id_o"
        else:
            return None

    def get_first_player(self):
        if self.first_player is None:
            i = random.randint(0, 1)
            first_player = [self.user_id_x, self.user_id_o][i]
            self.first_player = first_player
            db.session.commit()
        else:
            first_player = self.first_player
        return first_player

    def player_to_move(self):
        players = [self.user_id_x, self.user_id_o]
        last_move = db.session.query(Move).filter_by(game_id=self.id).order_by(Move.id.desc()).first()
        if last_move is None:
            next_player = self.get_first_player()
        else:
            last_player = last_move.user_id
            players.remove(last_player)
            next_player = players[0]
        return next_player

    @staticmethod
    def game_end(x_positions, o_positions):
        winnings = [[1, 2, 3],
                    [4, 5, 6],
                    [7, 8, 9],
                    [1, 4, 7],
                    [2, 5, 8],
                    [3, 6, 9],
                    [1, 5, 9],
                    [3, 5, 7]]

        x_positions.sort()
        o_positions.sort()

        for w_list in winnings:
            check_x = all(item in x_positions for item in w_list)
            check_o = all(item in o_positions for item in w_list)
            if check_x:
                print("X wins")
                return "x"
            if check_o:
                print("O wins")
                return "o"

        if len(x_positions) + len(o_positions) == 9:
            print("DRAW")
            return "d"
        else:
            return False
