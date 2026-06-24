from flask import Flask
from models import db

app= Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///trekking.db'
app.config['SECRET_KEY'] = 'TREKKEY'

db.init_app(app)