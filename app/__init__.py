import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from instance.config import Config

app = Flask(__name__)
app.config.from_object(Config)
login = LoginManager(app)
db = SQLAlchemy(app)
        
from app import routes, models

db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
if 'sqlite' in Config.SQLALCHEMY_DATABASE_URI and not os.path.exists(db_path):
    with app.app_context():
        print(f"Database does not exist at {db_path}. Creating...")
        db.create_all()
        print("Database and tables created successfully.")