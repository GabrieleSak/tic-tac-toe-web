from flask import Flask, session, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from uuid import uuid4, UUID
from sqlalchemy.dialects.postgresql import UUID
from config import Config

# from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)


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


class Move(db.Model):
    __tablename__ = "moves"
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
    # game = db.session.query(Game).filter(Game.user_id_x == None).first()


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


@app.route('/game/<int:game_id>', methods=['GET', 'POST'])
def game(game_id):
    game = Game.query.get(game_id)
    player_x = game.user_id_x
    player_o = game.user_id_o
    if request.method == 'POST':
        redirect(url_for("moves", game_id=game_id))
    return render_template("game.html", game_id=game_id, player_x=player_x, player_o=player_o)


@app.route('/game/<int:game_id>/moves', methods=['GET', 'POST'])
def moves(game_id):
    print("moves")
    current_game = Game.query.get(game_id)
    player_x = current_game.user_id_x
    player_o = current_game.user_id_o
    if request.method == 'POST':
        position = request.form.get("position")
        print(position)
    return render_template("game.html", game_id=game_id, player_x=player_x, player_o=player_o)

if __name__ == "__main__":
    app.run(debug=True)
