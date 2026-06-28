from flask import Flask
from models import db
from flask_login import LoginManager

app= Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///trekking.db'
app.config['SECRET_KEY'] = 'TREKKEY'

db.init_app(app)
login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view='login'
from routes import *

if __name__ == '__main__':
    app.run(debug=True)