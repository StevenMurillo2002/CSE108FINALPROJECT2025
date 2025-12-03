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



if __name__ == '__main__':
    app.run(debug=True)
