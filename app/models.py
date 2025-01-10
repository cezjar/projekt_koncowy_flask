from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.orm import declarative_base
from app import db
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash,check_password_hash
from app import login
from flask_login import UserMixin
from hashlib import md5

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('users.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('users.id'),
              primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(64), index=True, unique=True)
    email = sa.Column(sa.String(120), index=True, unique=True)
    password_hash = sa.Column(sa.String(256), nullable=True)
    about_me = sa.Column(sa.String(1024))
    name = sa.Column(sa.String(64))
    interests = sa.Column(sa.String(512))
    last_seen = sa.Column(sa.String(512))

    posts = so.relationship('Post', back_populates='author')
    comments = so.relationship('Comment', back_populates='author')

    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        hash = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://api.dicebear.com/9.x/notionists/svg?seed={hash}?size={size}'
    

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None
    
    def is_not_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )

    def user_posts(self):
        return sa.select(Post).where(Post.user_id == self.id).order_by(Post.timestamp.desc())

    def select_users_query(self): 
        return sa.select(User)

    def all_users(self):
        return db.session.scalars(sa.select(User)).all()

    def __repr__(self):
        return f'<User {self.username}>'
    

class Post(db.Model):
    __tablename__ = 'posts'
    
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String(140))
    timestamp = sa.Column(sa.DateTime, index=True, default=lambda: datetime.now(timezone.utc) + timedelta(hours=1))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), index=True)

    author = so.relationship('User', back_populates='posts')
    comments = so.relationship('Comment', back_populates='post')

    def __repr__(self):
        return f'<Post {self.body}>'
    


class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.String(512))
    timestamp = sa.Column(sa.DateTime, index=True, default=lambda: datetime.now(timezone.utc) + timedelta(hours=1))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), index=True)
    post_id = sa.Column(sa.Integer, sa.ForeignKey('posts.id'), index=True)

    author = so.relationship('User', back_populates='comments')
    post = so.relationship('Post', back_populates='comments')

    def __repr__(self):
        return f'<Comment {self.body[:20]}>'
    
    def edit(self, new_body):
        self.body = new_body
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def get_author(self):
        return self.author

    def get_post(self):
        return self.post

    def get_timestamp(self):
        return self.timestamp