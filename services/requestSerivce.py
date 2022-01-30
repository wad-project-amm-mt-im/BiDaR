from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime

from services.demographicsService import demographics_service_1, demographics_service_2
from services.gamesService import video_games_service_1, video_games_service_2, video_games_service_3
from services.recommendationService import recommendation_system
from setup import db
from models import Interest, User
from utils import COUNTRIES, INGREDIENTS

main = Blueprint('main', __name__)


@main.route('/')
@login_required
def index():
    return render_template('search.html', name=current_user.name)


@main.route('/profile')
@login_required
def profile():
    # load the profile page with all data about user
    interests = Interest.query.with_entities(Interest.interest).filter_by(user_id=current_user.id).all()
    interests_value = []
    if interests:
        interests_value = [i.interest for i in interests]

    return render_template('profile.html', name=current_user.name, email=current_user.email, gender=current_user.gender,
                           state=current_user.state,
                           birthday=datetime.strftime(current_user.birthday, '%d-%m-%Y'),
                           interests_value=interests_value)


@main.route('/profile_add_interest', methods=['POST'])
@login_required
def add_interest():
    interest_name = request.form.get('interest')
    check_exists = Interest.query.filter_by(user_id=current_user.id, interest=interest_name).first()
    if not check_exists:
        new_interest = Interest(user_id=current_user.id, interest=interest_name)
        db.session.add(new_interest)
        db.session.commit()

    return redirect(url_for('main.profile'))


@main.route('/profile_remove_interest', methods=['POST'])
@login_required
def remove_interest():
    interest_name = request.form.get('interest_to_delete')
    Interest.query.filter_by(user_id=current_user.id, interest=interest_name).delete()
    db.session.commit()

    return redirect(url_for('main.profile'))


@main.route('/profile_update', methods=['POST'])
@login_required
def update():
    # update user data
    new_email = request.form.get('email')
    new_name = request.form.get('name')
    new_gender = request.form.get('gender')
    new_state = request.form.get('state')
    new_birthday = request.form.get('date')
    if new_birthday:
        try:
            new_birthday = datetime.strptime(new_birthday, '%d-%m-%Y')
        except ValueError:
            flash('Birthday bad format!')
            return redirect(url_for('main.profile'))

    user = User.query.filter_by(email=new_email).first()
    if user and current_user.email != new_email:
        flash('Email address already exists!')
        return redirect(url_for('main.profile'))

    current_user.email = new_email
    current_user.name = new_name
    current_user.gender = new_gender
    current_user.birthday = new_birthday
    current_user.state = new_state
    if request.form.get('password'):
        new_password = generate_password_hash(request.form.get('password'), method='sha256')
        current_user.password = new_password
    db.session.commit()

    return redirect(url_for('main.profile'))


@main.route('/search')
@login_required
def search():
    return render_template('search.html', name=current_user.name)


@main.route('/search', methods=['POST'])
@login_required
def get_query():
    # main page for query big data
    query = request.form.get('query')
    return render_template('search.html', name=current_user.name, query=query)


@main.route('/recommendations')
@login_required
def recommendations():
    return render_template('recommendation.html', name=current_user.name, ingredients_list=INGREDIENTS)


@main.route('/recommendations', methods=['POST'])
@login_required
def post_recommendations():
    button = request.form.get('button')
    ingredients = request.form.getlist('ingredients')

    if button == 'button_cloud':
        url = recommendation_system(ingredients, '0')
        return render_template('recommendation.html', name=current_user.name, ingredients_list=INGREDIENTS, url=url)
    elif button == 'button_recommendation':
        df = recommendation_system(ingredients, '1')
        return render_template('recommendation.html', name=current_user.name, ingredients_list=INGREDIENTS,
                               tables=[df.to_html(classes='table data')], titles=df.columns.values)

    return render_template('recommendation.html', name=current_user.name, ingredients_list=INGREDIENTS)


@main.route('/demographics')
@login_required
def demographics():
    return render_template('demographics.html', name=current_user.name, countries_list=COUNTRIES)


@main.route('/demographics', methods=['POST'])
@login_required
def post_demographics():
    countries = request.form.getlist('countries')
    service = request.form.get('services')
    info = request.form.get('information')

    if service == "service1":
        url = demographics_service_1(countries, info)
    else:
        fertility_no = request.form.get('fertility_no')
        democracy_no = request.form.get('democracy_no')
        life_no = request.form.get('life_no')
        url = demographics_service_2(countries, info, [fertility_no, democracy_no, life_no])

    return render_template('demographics.html', name=current_user.name, countries_list=COUNTRIES, url=url)


@main.route('/games')
@login_required
def games():
    return render_template('games.html', name=current_user.name, countries_list=COUNTRIES)


@main.route('/games', methods=['POST'])
@login_required
def post_games():
    button = request.form.get('button')
    exclude_countries = request.form.getlist("exclude_countries")
    exclude_continents = request.form.getlist("exclude_continents")
    if button == 'button_countries':
        chart = video_games_service_1(exclude_countries, exclude_continents)
        return render_template('games.html', name=current_user.name, countries_list=COUNTRIES, graphJSON=chart)
    elif button == 'button_continents':
        svg = video_games_service_2(exclude_countries, exclude_continents)
        return render_template('games.html', name=current_user.name, countries_list=COUNTRIES, svg=svg)
    else:
        countries_compare1 = request.form.get("countries_compare1")
        countries_compare2 = request.form.get("countries_compare2")
        url = video_games_service_3([countries_compare1, countries_compare2])

    return render_template('games.html', name=current_user.name, countries_list=COUNTRIES, url=url)
