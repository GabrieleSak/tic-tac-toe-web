from flask import Flask, session, render_template
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
        print(game_id)
    else:
        new_game = Game(user_id_x=user_id)
        db.session.add(new_game)
        db.session.commit()
        game_id = new_game.id
        print("New game ", game_id)

    return render_template("index.html", user_id=user_id)


if __name__ == "__main__":
    app.run(debug=True)
