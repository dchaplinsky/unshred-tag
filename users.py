import datetime

import flask_login
from flask import g
from social_flask.routes import social_auth
from social_flask_mongoengine.models import init_social

from models import User


def init_social_login(app, db):
    app.register_blueprint(social_auth)
    init_social(app, db)

    login_manager = flask_login.LoginManager()
    login_manager.login_view = 'index'
    login_manager.login_message = ''
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(userid):
        try:
            user = User.objects.get(id=userid)
            if user:
                user.last_login = datetime.datetime.now()
                user.save()
            return user
        except (TypeError, ValueError, User.DoesNotExist):
            pass

    @app.before_request
    def global_user():
        g.user = flask_login.current_user

    @app.context_processor
    def inject_user():
        try:
            return {'user': g.user}
        except AttributeError:
            return {'user': None}
