from flask import render_template, flash, redirect, url_for, request
from app import app
from app import db
from app.models import User, Post
import sqlalchemy as sa
from flask_login import current_user, login_user
from flask_login import logout_user
from datetime import datetime, timezone




@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])

def index():
    if current_user.is_authenticated:
        print(current_user.following_count())
        if request.method == 'POST':
            post_body = request.form.get('post')
            if post_body:
                post = Post(body=post_body, author=current_user)
                db.session.add(post)
                db.session.commit()
                flash('Opublikowałeś wpis!')
                return redirect(url_for('index'))

        page = request.args.get('page', 1, type=int)
        posts = db.paginate(
            current_user.following_posts(),
            page=page,
            per_page=app.config['POSTS_PER_PAGE'],
            error_out=False
        )

        next_url = url_for('index', page=posts.next_num) if posts.has_next else None
        prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None

        return render_template(
            'index.html',
            title='Home',
            posts=posts.items,
            next_url=next_url,
            prev_url=prev_url
        )
    return redirect(url_for('login'))

@app.route('/user/<username>')
def user(username):
    if current_user.is_authenticated:
        user = db.first_or_404(sa.select(User).where(User.username == username))
        posts = [
            {'author': user, 'body': 'Test post #1'},
            {'author': user, 'body': 'Test post #2'}
        ]
        user_last_seen = user.last_seen
        user_about_me = user.about_me
        can_edit = current_user.username == username

        return render_template('user.html', user=user, posts=posts, user_last_seen=user_last_seen, user_about_me=user_about_me, can_edit=can_edit)
    
    return redirect(url_for('login'))



@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_user.username = request.form.get('username', '').strip()
        current_user.about_me = request.form.get('about_me', '').strip()
        db.session.commit()
        flash('Zapisano zmiany', 'success')
        return redirect(url_for('user', username=current_user.username))

    return render_template('edit_profile.html', user=current_user)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print('User already authenticated, redirecting to index.')
        return redirect(url_for('index'))
    
    errors = {}

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember_me = request.form.get('remember_me', 'off')

        # Basic validation logic
        if not username:
            errors['username'] = 'Login jest wymagany!'
        if not password:
            errors['password'] = 'Hasło jest wymagane!'

        if not errors:
            user = db.session.scalar(
                sa.select(User).where(User.username == username))
            if user is None or not user.check_password(password):
                print(f'Failed login attempt for username: {username}')
                flash('Invalid username or password', 'error')
                return redirect(url_for('login'))
            
            login_user(user, remember=remember_me)
            print(f'User {username} logged in successfully.')
            return redirect(url_for('index'))
        
    return render_template('login.html', title='Zaloguj się', errors=errors)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        print('User already authenticated, redirecting to index.')
        return redirect(url_for('index'))
    
    errors = {}

    if request.method == 'POST': 
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not username:
            errors['username'] = 'Login jest wymagany!'
        if not email:
            errors['email'] = 'Email jest wymagany!'
        if not password:
            errors['password'] = 'Hasło jest wymagane!'

        if not errors:
            existing_user_by_username = db.session.scalar(
                sa.select(User).where(User.username == username)
            )
            existing_user_by_email = db.session.scalar(
                sa.select(User).where(User.email == email)
            )
            
            if existing_user_by_username:
                errors['username'] = 'Nazwa użytkownika jest zajęta.'
                return render_template('register.html', title='Zarejestruj się', errors=errors)
            elif existing_user_by_email:
                errors['email'] = 'Email jest zajęty.'
                return render_template('register.html', title='Zarejestruj się', errors=errors)
            else:
                new_user = User(username=username, email=email)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                flash('Gratulacje, udało Ci się zarejestrować!', 'success')
            return redirect(url_for('login'))

        return render_template('register.html', title='Zarejestruj się', errors=errors)


    return render_template('register.html', title='Zarejestruj się', errors=errors)  


@app.route('/follow/<username>', methods=['POST'])
def follow(username):
    if current_user.is_authenticated:
        request.form.get('unfollow')
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('user', username=username))

    return(redirect(url_for('login')))

@app.route('/unfollow/<username>', methods=['POST'])
def unfollow(username):
    if current_user.is_authenticated:
        request.form.get('unfollow')
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.')
        return redirect(url_for('user', username=username))

    return(redirect(url_for('login')))