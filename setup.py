from email.mime import application
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()


def create_app():
    application = Flask(__name__)

    application.config['SECRET_KEY'] = 'secret-key-tanana'
    application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(application)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(application)

    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from services.authenticationService import auth as auth_blueprint
    application.register_blueprint(auth_blueprint)

    from services.search_services.search_service_api import searchModule as search_blueprint
    application.register_blueprint(search_blueprint)
    
    from services.visualization_service.vizualization_service import vizualization as vizualization_blueprint
    application.register_blueprint(vizualization_blueprint)

    from services.requestSerivce import main as main_blueprint
    application.register_blueprint(main_blueprint)


    return application


myapp = create_app()

