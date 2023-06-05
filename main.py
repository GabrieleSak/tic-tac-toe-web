import random

from flask import Flask, session, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from uuid import uuid4, UUID
from sqlalchemy.dialects.postgresql import UUID
from flask_migrate import Migrate

from config import Config

# from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String())
    moves = db.relationship("Move")


class Game(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    user_id_x = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    user_id_o = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    moves = db.relationship("Move")
    first_player = db.Column(db.String())


class Move(db.Model):
    __tablename__ = "moves"
    __table_args__ = (db.UniqueConstraint('game_id', 'position'),)
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    move_no = db.Column(db.Integer)
    position = db.Column(db.Integer)


with app.app_context():
    db.create_all()
    db.session.commit()


def is_part_of_game(user_id):
    if (db.session.query(Game).filter_by(user_id_x=user_id).first() is not None
            or db.session.query(Game).filter_by(user_id_o=user_id).first() is not None):
        return True
    return False


def get_game_id(user_id):
    if db.session.query(Game).filter_by(user_id_x=user_id).first() is not None:
        game_id = [r.id for r in db.session.query(Game).filter_by(user_id_x=user_id)]
    elif db.session.query(Game).filter_by(user_id_o=user_id).first() is not None:
        game_id = [r.id for r in db.session.query(Game).filter_by(user_id_o=user_id)]
    return game_id[0]


def game_waiting_second_player():
    game_x = db.session.query(Game).filter(Game.user_id_x == None).first()
    game_o = db.session.query(Game).filter(Game.user_id_o == None).first()
    if game_x is not None:
        return game_x.id, "user_id_x"
    elif game_o is not None:
        return game_o.id, "user_id_o"
    else:
        return None


@app.route('/')
def home():
    session.permanent = True
    if 'user_id' in session:
        user_id = session['user_id']
    else:
        new_user = User(name="Vardenis")
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        user_id = session['user_id']
    # check if user is in in-progress game
    if is_part_of_game(user_id):
        game_id = get_game_id(user_id)
        print("You are part of the game ", game_id)
        return redirect(url_for("game", game_id=game_id))
    else:
        # check if there is a game waiting for player 2
        if game_waiting_second_player():
            available_spot = game_waiting_second_player()
            game = Game.query.get(available_spot[0])
            player_type = available_spot[1]
            setattr(game, player_type, user_id)
            db.session.commit()
            print("You joined game ", game.id)
            return redirect(url_for("game", game_id=game.id))
        else:
            new_game = Game(user_id_x=user_id)
            db.session.add(new_game)
            db.session.commit()
            game_id = new_game.id
            print("Waiting for second player to join game: ", game_id)
            return redirect(url_for("game", game_id=game_id))
    return render_template("index.html", user_id=user_id)


def first_player(game_id):
    game = Game.query.get(game_id)
    if game.first_player is None:
        i = random.randint(0, 1)
        first_player = [game.user_id_x, game.user_id_o][i]
        game.first_player = first_player
        db.session.commit()
    else:
        first_player = game.first_player
    return first_player


def player_to_move(game_id):
    game = Game.query.get(game_id)
    players = [game.user_id_x, game.user_id_o]
    last_move = db.session.query(Move).filter_by(game_id=game_id).order_by(Move.id.desc()).first()
    if last_move is None:
        next_player = first_player(game_id)
    else:
        last_player = last_move.user_id
        players.remove(last_player)
        next_player = players[0]
    return next_player


def is_move_legal(game_id, move):
    if db.session.query(Move).filter_by(game_id=game_id, position=move).first() is None:
        return True
    else:
        return False


@app.route('/game/<int:game_id>', methods=['GET'])
def game(game_id):
    game = Game.query.get(game_id)
    player_x = game.user_id_x
    player_o = game.user_id_o
    x_moves = db.session.query(Move).filter_by(game_id=game_id, user_id=player_x).all()
    x_positions = [move.position for move in x_moves]
    o_moves = db.session.query(Move).filter_by(game_id=game_id, user_id=player_o).all()
    o_positions = [move.position for move in o_moves]

    # last move
    last_move = db.session.query(Move).filter_by(game_id=game_id).order_by(Move.id.desc()).first()
    if last_move is None:
        last_move_pos = ""
    else:
        last_move_pos = last_move.position

    if player_x is None or player_o is None:
        print("waiting for a second player")
    else:
        next_player = player_to_move(game_id)
        return render_template("game.html", game_id=game_id, player_x=player_x, player_o=player_o,
                               x_positions=x_positions,
                               o_positions=o_positions, next_player=next_player, first_player=game.first_player,
                               last_pos=last_move_pos)
    return render_template("game.html", game_id=game_id, player_x=player_x, player_o=player_o,
                           x_positions=x_positions,
                           o_positions=o_positions, first_player=game.first_player)


@app.route('/game/<int:game_id>/moves', methods=['POST'])
def moves(game_id):
    print("moving")
    if request.method == 'POST':
        next_player = request.args.get('next_player')
        print("next", next_player)
        print(str(session['user_id']))
        print(str(session['user_id']) == next_player)
        if str(session['user_id']) == next_player:
            position = request.form.get("position")
            print("pos", position)
            if position in ["X", "O"]:
                print("Illegal move!")
            else:
                new_move = Move(
                    game_id=game_id,
                    user_id=session['user_id'],
                    position=position
                )
                db.session.add(new_move)
                db.session.commit()
    return redirect(url_for("game", game_id=game_id))


if __name__ == "__main__":
    app.run(debug=True)
