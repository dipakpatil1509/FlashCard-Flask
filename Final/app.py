import os
from flask import Flask, jsonify, redirect, session, url_for, flash
from flask_restful import Api
from sqlalchemy import exc
from application.database import db
from flask_login import LoginManager
from flask_migrate import Migrate
from application.error import APIException


app = None
api = None

base_dir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = False
    SQLITE_DB = None
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class LocalDevelopment(Config):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static", static_url_path="")
    app.logger.debug("Starting Server")
    app.config.from_object(LocalDevelopment)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SECRET_KEY'] = '21f1004451abcd.'
    app.config['SECURITY_PASSWORD_SALT'] = "21f100##4451@$"
    db.init_app(app)
    

    app.app_context().push()
    api = Api(app)
    return app, api


app, api = create_app()

migrate = Migrate(app, db, render_as_batch=True)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

from application.models.user_mode import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.errorhandler(APIException)
def handle_custom_exception(err):
    return jsonify(err.error), 400

@app.errorhandler(exc.SQLAlchemyError)
def handle_db_exceptions(error):
    db.session.rollback()

@app.errorhandler(TypeError)
def all_exception_handler(error):
    return dict(error_code=400, error_message=str(error))

@app.before_first_request
def before_req():
    if not session.get('user'):
        flash('Not so fast! Kindly login to view that page')
    return redirect(url_for('auth.login'))


from application.routes.auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from application.routes.profile import profile as profile_blueprint
app.register_blueprint(profile_blueprint)

from application.routes.deck import deck as deck_blueprint
app.register_blueprint(deck_blueprint)

from application.routes.card import card as card_blueprint
app.register_blueprint(card_blueprint)

from application.routes.review import review as review_blueprint
app.register_blueprint(review_blueprint)

if __name__ == "__main__":
    db.create_all()
    app.run()
