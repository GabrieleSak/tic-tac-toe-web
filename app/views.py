from app import app, db
from functools import wraps
from flask import session, render_template, redirect, url_for, request, abort, jsonify
from sqlalchemy import or_, and_
from .models.game import Game
from .models.user import User
from .models.move import Move


def player_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        game_id = kwargs['game_id']
        games = [g.id for g in db.session.query(Game).filter(
            or_(Game.user_id_x == session['user_id'], Game.user_id_o == session['user_id']))]
        if game_id not in games:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


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
    current_user = User.query.get(user_id)
    if current_user.is_part_of_game():
        game_id = current_user.get_game_id()
        print("You are part of the game ", game_id)
        return redirect(url_for("game", game_id=game_id))
    else:
        # check if there is a game waiting for player 2
        if Game.game_waiting_second_player():
            available_spot = Game.game_waiting_second_player()
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


@app.route('/game/<int:game_id>', methods=['GET'])
@player_only
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
    print("last posi", last_move_pos)

    if game.game_end(x_positions, o_positions):
        result = game.game_end(x_positions, o_positions)
        print(result)
        game.result = result
        db.session.commit()
        return render_template("game_end.html", game_id=game_id, player_x=player_x, player_o=player_o,
                               x_positions=x_positions,
                               o_positions=o_positions, last_pos=last_move_pos, res=result)

    if player_x is None or player_o is None:
        print("waiting for a second player")
    else:
        next_player = game.player_to_move()
        print(type(next_player))
        print(game.first_player)
        print(session["user_id"])
        print(game.first_player == str(session["user_id"]))

        return render_template("game.html", game_id=game_id, player_x=player_x, player_o=player_o,
                               x_positions=x_positions,
                               o_positions=o_positions, next_player=next_player, first_player=game.first_player,
                               last_pos=last_move_pos)

    return render_template("game.html", game_id=game_id, player_x=player_x, player_o=player_o,
                           x_positions=x_positions,
                           o_positions=o_positions, first_player=game.first_player)


@app.route('/current_game', methods=['GET'])
def turn():
    current_user = User.query.get(session['user_id'])
    game_id = current_user.get_game_id()
    current_game = Game.query.get(game_id)
    player_to_move = current_game.player_to_move()
    if session['user_id'] == player_to_move:
        is_your_move = True
    else:
        is_your_move = False
    if request.accept_mimetypes['application/json']:
        return jsonify({"your_move": is_your_move})
    return redirect(url_for('game'))


@app.route('/game/<int:game_id>/moves', methods=['POST'])
@player_only
def moves(game_id):
    if request.method == 'POST':
        current_player = request.args.get('current_player')
        if str(session['user_id']) == current_player:
            position = request.form.get("position")
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
