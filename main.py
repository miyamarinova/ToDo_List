from flask import Flask, render_template, request, redirect, url_for, abort, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm
from sqlalchemy.orm import relationship
import os
from sqlalchemy import Table, Column, Integer, ForeignKey

#--- Flask App -----------------------#
app = Flask(__name__)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

Bootstrap(app)

#--- setup SQL DB -----------------------#
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)

class Todo(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name_task = db.Column(db.String(250))
    complete = db.Column(db.Boolean)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = relationship("Users", back_populates='tasks')

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    name = db.Column(db.String)
    tasks = relationship("Todo", back_populates='user')

db.create_all()

@app.route('/')
def home():
    if not current_user.is_authenticated:
        return render_template('index.html')
    else:

        todo_list = Todo.query.all()
        return render_template('index.html', todo_list=todo_list)

@app.route('/add',methods=['POST', 'GET'])
def add():
    name = request.form.get('name')
    user_id = current_user.id
    new_task = Todo(name_task=name, user_id=user_id, complete=False)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for("home"))

@app.route('/update/<int:id>')
def update(id):
    task_to_update = Todo.query.get(id)
    task_to_update.complete = not task_to_update.complete
    db.session.commit()
    return redirect(url_for("home"))

@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get(id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(url_for("home"))

#Register new user, take the information that is inputted in register.html and create a new object User to save into the users databas
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hash_salt_password = generate_password_hash(form.password.data, method='pbkdf2:sha256',salt_length=8)
        new_user = Users(
            email=form.email.data,
            password=hash_salt_password,
            name=form.name.data
        )
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            flash("You've already signed up with this email, log in instead.")
            return redirect("login")
        else:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("home"))
    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower(),
        password = form.password.data
        user = Users.query.filter_by(email=form.email.data).first()

        if not user:
            flash("Wrong email. Please, try again!")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again!")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html", form=form, current_user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
