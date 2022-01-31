from datetime import datetime

from flask import Blueprint, request, jsonify, send_file
from flask_login import current_user
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import User, Interest
from services.demographicsService import demographics_service_1, demographics_service_2
from services.gamesService import video_games_service_2, video_games_service_1, video_games_service_3
from services.recommendationService import recommendation_system
from setup import db
from utils import check

rest = Blueprint('rest', __name__)


@rest.route('/rest/login', methods=['POST'])
def login():
    email = request.values.get('email')
    password = request.values.get('password')

    if email and password:
        user = User.query.filter_by(email=email).first()
        if not user:
            resp = jsonify({'message': 'Bad Request - invalid credentials'})
            resp.status_code = 400

        if check_password_hash(user.password, password):
            login_user(user)
            resp = jsonify({'message': 'You are logged in successfully'})
        else:
            resp = jsonify({'message': 'Bad Request - invalid password'})
            resp.status_code = 400
    else:
        resp = jsonify({'message': 'Bad Request - invalid parameters'})
        resp.status_code = 400

    return resp


@rest.route('/rest/register', methods=['POST'])
def register():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')
    gender = request.form.get('gender')
    birthday = request.form.get('date')
    state = request.form.get('state')
    if birthday:
        try:
            birthday = datetime.strptime(birthday, '%Y-%m-%d')
        except ValueError:
            resp = jsonify({'message': 'Bad Request - date wrong format!Try year-month-day.'})
            resp.status_code = 400
            return resp

    if check(email) and name and password and gender and birthday and state:
        user = User.query.filter_by(email=email).first()
        if user:
            resp = jsonify({'message': 'Bad Request - email already exists!'})
            resp.status_code = 400
        else:
            new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'), gender=gender, state=state, birthday=birthday)
            db.session.add(new_user)
            db.session.commit()
            resp = jsonify({'message': 'User registered'})
            resp.status_code = 201
    else:
        resp = jsonify({'message': 'Bad Request - wrong parameters!'})
        resp.status_code = 400
    return resp


@rest.route('/rest/info_update', methods=['PUT'])
def info_update():
    if not current_user.is_authenticated:
        resp = jsonify({'message': 'Login first'})
        resp.status_code = 400
        return resp

    new_email = request.form.get('email')
    new_name = request.form.get('name')
    new_gender = request.form.get('gender')
    new_state = request.form.get('state')
    new_birthday = request.form.get('date')
    new_password = generate_password_hash(request.form.get('password'), method='sha256')
    if new_birthday:
        try:
            new_birthday = datetime.strptime(new_birthday, '%d-%m-%Y')
        except ValueError:
            resp = jsonify({'message': 'Bad Request - date wrong format!Try day-month-year.'})
            resp.status_code = 400
            return resp

    if check(new_email) and new_name and new_password and new_gender and new_birthday and new_state:
        if current_user.email != new_email:
            user = User.query.filter_by(email=new_email).first()
            if user:
                resp = jsonify({'message': 'Email is taken!'})
                resp.status_code = 400
                return resp
        current_user.email = new_email
        current_user.name = new_name
        current_user.gender = new_gender
        current_user.birthday = new_birthday
        current_user.state = new_state
        current_user.password = new_password
        db.session.commit()
        resp = jsonify({'message': 'User ' + current_user.email + ' updated!'})
        resp.status_code = 201
    else:
        resp = jsonify({'message': 'Bad Request - wrong parameters!'})
        resp.status_code = 400
    return resp


@rest.route('/rest/get_user', methods=['GET'])
def get_user():
    if not current_user.is_authenticated:
        resp = jsonify({'message': 'Login first'})
        resp.status_code = 400
        return resp

    resp = jsonify({'email': current_user.email})
    resp.status_code = 201
    return resp


@rest.route('/rest/logout', methods=['GET'])
def logout():
    if not current_user.is_authenticated:
        resp = jsonify({'message': 'Login first'})
        resp.status_code = 400
        return resp

    logout_user()
    resp = jsonify({'message': 'User logged out!'})
    resp.status_code = 201
    return resp


@rest.route('/rest/get_users', methods=['GET'])
def get_users():
    users = User.query.all()
    u = [user.email for user in users]
    resp = jsonify({'users': u})
    resp.status_code = 201
    return resp


@rest.route('/rest/interests', methods=['GET'])
def get_interests():
    if not current_user.is_authenticated:
        resp = jsonify({'message': 'Login first'})
        resp.status_code = 400
        return resp

    interests = Interest.query.with_entities(Interest.interest).filter_by(user_id=current_user.id).all()
    if interests:
        interests_value = [i.interest for i in interests]
    else:
        interests_value = 'No interests'
    resp = jsonify({'Interests': interests_value})
    resp.status_code = 201
    return resp


@rest.route('/rest/interests', methods=['POST'])
def post_interests():
    if not current_user.is_authenticated:
        resp = jsonify({'message': 'Login first'})
        resp.status_code = 400
        return resp

    interest_name = request.values.get('interest')
    if interest_name:
        check_exists = Interest.query.filter_by(user_id=current_user.id, interest=interest_name).first()
        if not check_exists:
            new_interest = Interest(user_id=current_user.id, interest=interest_name)
            db.session.add(new_interest)
            db.session.commit()
            resp = jsonify({'message': 'Interest added!'})
            resp.status_code = 201
            return resp
    else:
        resp = jsonify({'message': 'Bad Request - wrong parameters!'})
        resp.status_code = 400
        return resp


@rest.route('/rest/interests', methods=['DELETE'])
def delete_interests():
    if not current_user.is_authenticated:
        resp = jsonify({'message': 'Login first'})
        resp.status_code = 400
        return resp

    interest_name = request.values.get('interest')
    if interest_name:
        check_exists = Interest.query.filter_by(user_id=current_user.id, interest=interest_name).first()
        if check_exists:
            Interest.query.filter_by(user_id=current_user.id, interest=interest_name).delete()
            db.session.commit()
            resp = jsonify({'message': 'Interest deleted!'})
            resp.status_code = 201
            return resp
    else:
        resp = jsonify({'message': 'Bad Request - wrong parameters!'})
        resp.status_code = 400
        return resp


@rest.route('/rest/demographics/<service>', methods=['POST'])
def demographics(service):
    if not current_user.is_authenticated:
        resp = jsonify({'message': 'Login first'})
        resp.status_code = 400
        return resp

    countries = request.values.getlist('countries')
    if countries and service in ['stackplot', 'lineplot', 'pieplot']:
        url = demographics_service_1(countries, service)
        return send_file(url, as_attachment=True, attachment_filename='test.jpg', mimetype='image/png')
    elif countries and service in ['min', 'max', 'avg']:
        fertility = request.form.get('fertility')
        democracy = request.form.get('democracy')
        life = request.form.get('life')
        if fertility and democracy and life:
            url = demographics_service_2(countries, service, [fertility, democracy, life])
            return send_file(url, as_attachment=True, attachment_filename='test.jpg', mimetype='image/png')
    else:
        resp = jsonify({'message': 'Incorrect param'})
        resp.status_code = 400
        return resp


@rest.route('/rest/games/<service_type>', methods=['GET'])
def games(service_type):
    if not current_user.is_authenticated:
        resp = jsonify({'message': 'Login first'})
        resp.status_code = 400
        return resp

    if service_type == 'countries':
        graph = video_games_service_1([], [])
        resp = jsonify(graph)
        resp.status_code = 400
        return resp
    elif service_type == 'continents':
        svg = video_games_service_2([], [])
        return send_file(svg, as_attachment=True, attachment_filename='test.jpg', mimetype='image/svg+xml')


@rest.route('/rest/games/compare', methods=['POST'])
def games_post():
    if not current_user.is_authenticated:
        resp = jsonify({'message': 'Login first'})
        resp.status_code = 400
        return resp

    countries = request.values.getlist('countries')
    if countries:
        url = video_games_service_3(countries)
        return send_file(url, as_attachment=True, attachment_filename='test.jpg', mimetype='image/png')
    else:
        resp = jsonify({'message': 'Incorrect params'})
        resp.status_code = 400
        return resp


@rest.route('/rest/recommendation/<type>', methods=['POST'])
def recommendation(type):
    if not current_user.is_authenticated:
        resp = jsonify({'message': 'Login first'})
        resp.status_code = 400
        return resp

    ingredients = request.values.getlist('ingredients')
    if ingredients:
        if type == 'table':
            df = recommendation_system(ingredients, '1')
            resp = jsonify(df.to_json(orient="records"))
            resp.status_code = 400
            return resp
        elif type == 'cloud':
            url = recommendation_system(ingredients, '0')
            return send_file(url, as_attachment=True, attachment_filename='test.jpg', mimetype='image/png')
    else:
        resp = jsonify({'message': 'Incorrect params'})
        resp.status_code = 400
        return resp


@rest.route('/rest/search/<topic>', methods=['GET'])
def search(topic):
    if not current_user.is_authenticated:
        resp = jsonify({'message': 'Login first'})
        resp.status_code = 400
        return resp
    # add search call
    pass
