from flask_sqlalchemy import SQLAlchemy 
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_admin import Admin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, current_user, login_required, login_user, logout_user
from sqlalchemy import select, and_


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.secret_key = 'keep it secret, keep it safe'




class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    display_name = db.Column(db.String(64), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def verify(self, password):
        return check_password_hash(self.password_hash, password)



class Ingredients(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    category = db.Column(db.String(64), nullable=True)


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    round_num = db.Column(db.Integer, default=1)
    active = db.Column(db.Boolean, default=True)

class PlayerGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    score = db.Column(db.Integer, default=0)
    user = db.relationship("User")

class GameRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    ingredients = db.Column(db.String(256))
    phase  = db.Column(db.String(32), default='submit')
    responses = db.relationship('Responses', backref='round', lazy=True)

class Responses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('game_round.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    text = db.Column(db.String(256))
    votes = db.Column(db.Integer, default=0)
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint('round_id', 'text', name='uniq_response_per_round'),
    )

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    round_id = db.Column(db.Integer, db.ForeignKey('game_round.id'), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    response_id = db.Column(db.Integer, db.ForeignKey('responses.id'), nullable=False)

 
    voter = db.relationship("User", foreign_keys=[voter_id])
    response = db.relationship("Responses", foreign_keys=[response_id])

    __table_args__ = (
        db.UniqueConstraint('round_id', 'voter_id', name='uniq_vote_per_round'),
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


from flask_admin.contrib.sqla import ModelView


admin = Admin(app, name='Admin View')
admin.add_view(ModelView(User,db.session))
admin.add_view(ModelView(Ingredients, db.session))
admin.add_view(ModelView(PlayerGame, db.session))
admin.add_view(ModelView(GameRound, db.session))
admin.add_view(ModelView(Responses, db.session))

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=["GET","POST"])
def login():
    # Already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Login
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        print(username, password)
        user = User.query.filter_by(username=username).first()
        if user is None or not user.verify(password):
            flash('Login failed, try again.', 'alert')
            return redirect(url_for('login'))
        if user and user.verify(password):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
     # If already logged in, skip signup
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        display_name = request.form.get('display_name') or username

        # Basic validation
        if not username or not password:
            flash("Username and password are required.", "alert")
            return redirect(url_for('signup'))
        
        # Check if username is taken
        existing = User.query.filter_by(username=username).first()
        if existing:
            flash('Username already taken, choose another.', 'alert')
            return redirect(url_for('signup'))
        
        # Create user with hashed and salted password
        user = User(username=username, display_name=display_name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/creategame')
@login_required

def creategame():
    newgame = Game(host_id = current_user.id, round_num = 1, active = True)
    # create a new game with the host being the current user who just clicked create game
    db.session.add(newgame)
    db.session.commit()

    gamehost = PlayerGame(game_id = newgame.id, user_id = current_user.id, score=0)
    # add the user to the game setting the game id and the user id to the current user, also setting their score to be 0
    db.session.add(gamehost)
    db.session.commit()

    return redirect(url_for('lobby', game_id = newgame.id))
    # put user into the lobby until the user is ready to start the game



@app.route('/gamelobby/<int:game_id>')
@login_required
def lobby(game_id):

    game = Game.query.get(game_id)
    if not game:
        return redirect(url_for('dashboard'))

    pg = PlayerGame.query.filter_by(game_id=game_id, user_id=current_user.id).first()
    if not pg:
        return redirect(url_for('dashboard'))

    round_started = GameRound.query.filter_by(game_id=game_id).first()
    if round_started:
        return redirect(url_for(
            "actualgame",
            game_id=game_id,
            round_id=round_started.id
        ))

    allplayers = (
        User.query
            .join(PlayerGame, PlayerGame.user_id == User.id)
            .filter(PlayerGame.game_id == game_id)
            .all()
    )
    return render_template(
        'gamelobby.html',
        game_id=game_id,
        allplayers=allplayers,
        host_id=game.host_id
    )

@app.route('/joingame', methods=['POST'])
@login_required
def joingamepost():
    game_id = request.form.get('game_id')
    # grab the room code from the user
    if not game_id:
        flash('Error: Invalid code, try again', 'alert')
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('joingame', game_id = game_id))

@app.route('/joingame/<int:game_id>')
@login_required
def joingame(game_id):
    game = Game.query.get(game_id)
   
    if not game:
        flash('Error: Invalid code, try again', 'alert')
        return redirect(url_for('dashboard'))
    # check to see if the lobby for the game exists 
    
    repeatplayer = PlayerGame.query.filter_by(game_id = game_id, user_id = current_user.id).first()
    if repeatplayer:
        flash("YOU ARE ALREADY IN THE GAME!!!!!!", 'alert')
        return redirect(url_for('dashboard'))

    limitplayers = PlayerGame.query.filter_by(game_id = game_id).all()
    if len(limitplayers) >= 4:
        flash("THIS GAME IS FULL LIL BRO", "alert")
        return redirect(url_for('dashboard'))
    


    newplayer = PlayerGame(game_id = game_id, user_id = current_user.id, score = 0)
    # create a new player by adding them to the game lobby and set the score = 0
    db.session.add(newplayer)
    db.session.commit()

    return redirect(url_for('lobby', game_id = game_id))

@app.route('/leavegame/<int:game_id>')
@login_required
def leavegame(game_id):
    game = Game.query.get(game_id)
    if game is None:
        flash("Game not found.", "alert")
        return redirect(url_for('dashboard'))

 
    pg = PlayerGame.query.filter_by(game_id=game_id, user_id=current_user.id).first()
    if pg is not None:
        db.session.delete(pg)

 
    if current_user.id == game.host_id:
        rounds = GameRound.query.filter_by(game_id=game_id).all()
        round_ids = [r.id for r in rounds]
        for r in rounds:
            Responses.query.filter_by(round_id=r.id).delete()

        Vote.query.filter(Vote.round_id.in_(round_ids)).delete(synchronize_session=False)
        GameRound.query.filter_by(game_id=game_id).delete()
        PlayerGame.query.filter_by(game_id=game_id).delete()
        db.session.delete(game)

        db.session.commit()
        return redirect(url_for('dashboard'))


    remaining = PlayerGame.query.filter_by(game_id=game_id).count()
    if remaining == 0:
        rounds = GameRound.query.filter_by(game_id=game_id).all()
        for r in rounds:
            Responses.query.filter_by(round_id=r.id).delete()
        GameRound.query.filter_by(game_id=game_id).delete()
        db.session.delete(game)

    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/kickplayer/<int:game_id>/<int:user_id>')
@login_required
def kickplayer(game_id, user_id):
    game = Game.query.get(game_id)
    if not game:
        return redirect(url_for('dashboard'))


    if current_user.id != game.host_id:
        return redirect(url_for('lobby', game_id=game_id))


    if user_id == game.host_id:
        return redirect(url_for('lobby', game_id=game_id))

    pg = PlayerGame.query.filter_by(game_id=game_id, user_id=user_id).first()
    if not pg:
        return redirect(url_for('lobby', game_id=game_id))

    db.session.delete(pg)
    db.session.commit()
    return redirect(url_for('lobby', game_id=game_id))


@app.route('/startgame/<int:game_id>')
@login_required

def startgame(game_id):
    game = Game.query.get(game_id)


    if not game:
        flash("Error: Your game was not found", "alert")
        return redirect(url_for("dashboard"))

    if current_user.id != game.host_id:
        flash("Only host can start game !!", "alert")
        return redirect(url_for('lobby', game_id=game_id))
    
    from random import sample
    ingredientslist = Ingredients.query.all()
    pickingredient = sample(ingredientslist, 3)
    ingredientpicked = ", ".join([i.name for i in pickingredient])

    round = GameRound(game_id = game_id, ingredients = ingredientpicked, phase = "submit")

    db.session.add(round)
    db.session.commit()

    return redirect(url_for('actualgame', game_id = game_id, round_id = round.id))

@app.route('/game/<int:game_id>/<int:round_id>')
@login_required
def actualgame(game_id, round_id):

    game = Game.query.get(game_id)
    if not game:
        flash("This game no longer exists.", "warning")
        return redirect(url_for('dashboard'))

    pg = PlayerGame.query.filter_by(game_id=game_id, user_id=current_user.id).first()
    if not pg:
        flash("You are no longer in this game.", "warning")
        return redirect(url_for('dashboard'))

    round_obj = GameRound.query.get_or_404(round_id)
    if round_obj.game_id != game_id:
        flash("Round does not belong to this game.", "alert")
        return redirect(url_for("dashboard"))

    return render_template(
        'actualgame.html',
        game_id=game_id,
        round=round_obj
    )
    

@app.route('/submitanswer/<int:game_id>/<int:round_id>', methods=["POST"])
@login_required

def submitanswer(game_id, round_id):
    answer = request.form.get('answer')

    if not answer:
        flash("Invalid answer, please try again!", "alert")
        return redirect(url_for('actualgame', game_id = game_id, round_id = round_id))
    
    answer_norm = " ".join(answer.strip().lower().split())
    existing = Responses.query.filter_by(round_id=round_id, text=answer_norm).first()

    if existing:
        flash("This answer has already been submitted, please try again!", "alert")
        return redirect(url_for('actualgame', game_id = game_id, round_id = round_id))
    
    new_answers = Responses(round_id = round_id, user_id = current_user.id, text = answer, votes = 0)
    db.session.add(new_answers)
    db.session.commit()     

    return redirect(url_for('votingwait', game_id = game_id, round_id = round_id))


@app.route('/votingwait/<int:game_id>/<int:round_id>')
@login_required
def votingwait(game_id, round_id):
    players = PlayerGame.query.filter_by(game_id=game_id).all()
    responses = Responses.query.filter_by(round_id=round_id).all()

    if len(players) == 0:
        flash("No players found for this game.", "alert")
        return redirect(url_for("dashboard"))


    if len(responses) >= len(players):
        return redirect(url_for('voting', game_id=game_id, round_id=round_id))

    return render_template(
        'votingwait.html',
        game_id=game_id,
        round_id=round_id,
        responses=responses,
        players=players
    )

@app.route('/votingwait_votes/<int:game_id>/<int:round_id>')
@login_required
def votingwait_votes(game_id, round_id):
    players = PlayerGame.query.filter_by(game_id=game_id).all()
    vote_count = Vote.query.filter_by(round_id=round_id).count()

    if len(players) == 0:
        flash("No players found for this game.", "alert")
        return redirect(url_for("dashboard"))

 
    if vote_count >= len(players):
        return redirect(url_for('endround', game_id=game_id, round_id=round_id))

    return render_template(
        'votingwait_votes.html',
        game_id=game_id,
        round_id=round_id,
        vote_count=vote_count,
        player_count=len(players),
        players = players
    )

@app.route('/continue/<int:game_id>/<int:current_round_id>')
@login_required
def continue_round(game_id, current_round_id):
    game = Game.query.get_or_404(game_id)


    next_round = (
        GameRound.query
        .filter(GameRound.game_id == game_id, GameRound.id > current_round_id)
        .order_by(GameRound.id.asc())
        .first()
    )
    if next_round:
        return redirect(url_for('actualgame', game_id=game_id, round_id=next_round.id))

 
    if game.round_num >= 3:
        return redirect(url_for('winner', game_id=game_id))

    game.round_num += 1

    from random import sample
    ingredientslist = Ingredients.query.all()
    ingredientpicked = ", ".join(i.name for i in sample(ingredientslist, 3))

    newround = GameRound(game_id=game_id, ingredients=ingredientpicked, phase="submit")
    db.session.add(newround)
    db.session.commit()

    latest = GameRound.query.filter_by(game_id=game_id).order_by(GameRound.id.desc()).first()
    return redirect(url_for('actualgame', game_id=game_id, round_id=newround.id))

@app.route('/voting/<int:game_id>/<int:round_id>')
@login_required

def voting(game_id, round_id):
    round = GameRound.query.get(round_id)
    responses = Responses.query.filter_by(round_id = round_id).all()

    return render_template('voting.html', game_id = game_id, round_id = round_id, responses = responses)


@app.route('/addvote/<int:game_id>/<int:round_id>/<int:response_id>', methods = ["POST"])
@login_required
def addvote(game_id, round_id, response_id):
    resp = Responses.query.get_or_404(response_id)


    if resp.user_id == current_user.id:
        flash("You cannot vote for your own answer!!", "alert")
        return redirect(url_for('voting', game_id=game_id, round_id=round_id))

    existing = Vote.query.filter_by(round_id=round_id, voter_id=current_user.id).first()
    if existing:
        flash("You already voted this round.", "alert")
        return redirect(url_for('votingwait_votes', game_id=game_id, round_id=round_id))


    db.session.add(Vote(round_id=round_id, voter_id=current_user.id, response_id=response_id))


    resp.votes += 1
    scorer = PlayerGame.query.filter_by(game_id=game_id, user_id=resp.user_id).first()
    if scorer:
        scorer.score += 1

    db.session.commit()

    return redirect(url_for('votingwait_votes', game_id=game_id, round_id=round_id))



@app.route('/endround/<int:game_id>/<int:round_id>')
@login_required
def endround(game_id, round_id):
    game = Game.query.get_or_404(game_id)


    if game.round_num >= 3:
        return redirect(url_for('winner', game_id=game_id))


    return redirect(url_for('roundresults', game_id=game_id, round_id=round_id))

@app.route('/roundresults/<int:game_id>/<int:round_id>')
@login_required
def roundresults(game_id, round_id):
    game = Game.query.get_or_404(game_id)
    players = PlayerGame.query.filter_by(game_id = game_id).order_by(PlayerGame.score.desc()).all()

    return render_template(
        "roundresults.html",
        game_id=game_id,
        round_id=round_id,
        players=players,
        round_num=game.round_num,
    )


@app.route('/winner/<int:game_id>')
@login_required
def winner(game_id):
    players = PlayerGame.query.filter_by(game_id = game_id).order_by(PlayerGame.score.desc()).all()

    if not players:
        return redirect(url_for('dashboard'))
    
    winner = max(players, key=lambda p:p.score)

    return render_template("winner.html", winner = winner, highestscore = winner.score, players = players)

@app.route('/waitround/<int:game_id>')
@login_required
def waitround(game_id):
    game = Game.query.get_or_404(game_id)

    game.round_num += 1

    from random import sample
    ingredientslist = Ingredients.query.all()
    ingredientpicked = ", ".join(i.name for i in sample(ingredientslist, 3))

    newround = GameRound(game_id=game_id, ingredients=ingredientpicked)
    db.session.add(newround)
    db.session.commit()

    return redirect(url_for('actualgame', game_id=game_id, round_id=newround.id))



    

    
if __name__ == '__main__':
    app.run(debug=True)
