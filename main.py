from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from uuid import uuid4, UUID
from sqlalchemy.dialects.postgresql import UUID

# from flask_migrate import Migrate

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/tic_tac_toe_db"
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


@app.route('/')
def home():
    return 'Tic Tac Toe'


if __name__ == "__main__":
    app.run(debug=True)
