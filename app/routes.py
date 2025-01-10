from flask import render_template, flash, redirect, url_for, request
from app import app
from app import db
from app.models import User, Post, Comment
import sqlalchemy as sa
from flask_login import current_user, login_user
from flask_login import logout_user
from datetime import datetime, timezone, timedelta




@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])

def index():
    if current_user.is_authenticated:
        if request.method == 'POST':
            if 'post' in request.form:
                post_body = request.form.get('post')
                if post_body:
                    post = Post(body=post_body, author=current_user)
                    db.session.add(post)
                    db.session.commit()
                    flash('Opublikowałeś wpis!')
                    return redirect(url_for('index'))
                
            elif 'add_comment' in request.form:
                comment_body = request.form.get('add_comment')
                post_id = request.form.get('post_id')
                if comment_body and post_id:
                    post = Post.query.get(post_id)
                    if post:
                        comment = Comment(body=comment_body, author=current_user, post=post)
                        db.session.add(comment)
                        db.session.commit()
                        flash('Opublikowałeś komentarz!')
                        return redirect(url_for('index'))
                    
            elif 'edit_comment' in request.form:
                comment_body = request.form.get('comment')
                comment_id = request.form.get('comment_id')
                print(f"comment_id: {comment_id}, comment_body: {comment_body}")
                if comment_body and comment_id:
                    comment = Comment.query.get(comment_id)
                    if comment:
                        comment.edit(comment_body)
                        db.session.commit()
                        print('test')
                        flash('Edytowałeś komentarz!')
                        return redirect(url_for('index'))
                    
            elif 'delete_comment' in request.form: 
                comment_id = request.form.get('comment_id')
                if comment_id:
                    comment = Comment.query.get(comment_id)
                    if comment:
                        comment.delete()
                        flash('Usunąłeś komentarz!')
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
        page = request.args.get('page', 1, type=int)
        posts = db.paginate(
            user.user_posts(),
            page=page,
            per_page=app.config['POSTS_PER_PAGE'],
            error_out=False
        )
        user_last_seen = user.last_seen
        user_about_me = user.about_me
        can_edit = current_user.username == username
        user_name = user.name
        user_interests = user.interests

        return render_template('user.html', user=user, posts=posts.items, user_last_seen=user_last_seen, user_about_me=user_about_me, can_edit=can_edit, user_name=user_name, user_interests=user_interests)
    
    return redirect(url_for('login'))



@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_user.username = request.form.get('username', '').strip()
        current_user.about_me = request.form.get('about_me', '').strip()
        current_user.name = request.form.get('name', '').strip()
        current_user.interests = request.form.get('interests', '').strip() 
        
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
                return render_template('register_next_step.html', username=username, email=email, password=password)

        return render_template('register.html', title='Zarejestruj się', errors=errors)
    return render_template('register.html', title='Zarejestruj się', errors=errors)  


@app.route('/register_next_step', methods=['POST'])
def register_next_step():
    about_me = request.form.get('about_me')
    interests = request.form.get('interests')
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    new_user = User(username=username, email=email, interests=interests, about_me=about_me, name = name)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    flash('Gratulacje, udało Ci się zarejestrować!', 'success')
    return redirect(url_for('login'))
        



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
            flash('Nie możesz zaobserwować samego siebie!')
            return redirect(url_for('user', username=username))
        
        if current_user.is_following(user):
            flash(f'Już obserwujesz {username}!')
            return redirect(url_for('user', username=username))
        
        current_user.follow(user)
        db.session.commit()
        flash(f'Obserwujesz {username}!')
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
            flash('Nie możesz odobserwować samego siebie!')
            return redirect(url_for('user', username=username))
        
        if current_user.is_not_following(user):
            flash(f'Nie obserwujesz {username}!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'Już nie obserwujesz {username}.')
        return redirect(url_for('user', username=username))

    return(redirect(url_for('login')))



@app.route('/explore')
def explore():
    if current_user.is_authenticated:
        user_list = current_user.all_users()
        user_count = len(user_list)
        page = request.args.get('page', 1, type=int)
        users = db.paginate(
                current_user.select_users_query(),
                page=page,
                per_page=app.config['USERS_PER_PAGE'],
                error_out=False
            )
        next_url = url_for('explore', page=users.next_num) if users.has_next else None
        prev_url = url_for('explore', page=users.prev_num) if users.has_prev else None
        return render_template(
            'explore.html',
            title='Home',
            users=users.items,
            user_count=user_count,
            next_url=next_url,
            prev_url=prev_url
        )
        