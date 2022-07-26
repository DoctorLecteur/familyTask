from flask import render_template, flash, redirect, url_for, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, SearchUserForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import Users
from werkzeug.urls import url_parse

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home Page')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = Users.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)

@app.route('/search_user', methods=['GET', 'POST'])
@login_required
def search():
    print('search user')
    search_from = SearchUserForm()
    if request.method == 'POST' and request.form.get('cancel') is not None:
        return redirect(url_for('user', username=current_user.username))
    if search_from.validate_on_submit():
        if search_from.username.data == "":
            flash('Enter empty username. Repeat search.')
            return redirect(url_for('search'))
        user_partner = Users.query.filter_by(username=search_from.username.data).first()
        if user_partner is None:
            flash('User {} not found. Repeat search.'.format(search_from.username.data))
            return redirect(url_for('search'))
        if user_partner == current_user:
            flash('You cannot create family only yourself!')
            return redirect(url_for('search'))
        current_user.create_family(user_partner)
        user_partner.create_family(current_user)
        db.session.commit()
        flash('You are creating family with {}!'.format(user_partner.username))
        return redirect(url_for('user', username=current_user.username))
    print('show modal form')
    return render_template('_modal_search_user.html', title='Search User', form=search_from)
