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
    password_hash = db.Column(db.String(256), nullable=False)

    def password(self,password):
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


from flask_admin.contrib.sqla import ModelView
app.secret_key = 'super secret key'

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
    return render_template('gamelobby.html', game_id = game_id)


@app.route('/joingame', methods=['POST'])
@login_required
def joingamepost():
    game_id = request.form.get('game_id')
    # grab the room code from the user
    return redirect(url_for('joingame', game_id = game_id))

@app.route('/joingame/<int:game_id>')
@login_required
def joingame(game_id):
    game = Game.query.get(game_id)
    # set the game equal to the game id 

    if not game:
        flash('Error: Game has not been found try again', 'alert')
        return redirect(url_for('dashboard'))
    # check to see if the lobby for the game exists 


    newplayer = PlayerGame(game_id = game_id, user_id = current_user.id, score = 0)
    # create a new player by adding them to the game lobby and set the score = 0
    db.session.add(newplayer)
    db.session.commit()

    return redirect(url_for('lobby', game_id = game_id))








if __name__ == '__main__':
    app.run(debug=True)
