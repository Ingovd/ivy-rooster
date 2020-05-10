from typing import Callable, Optional

from flask import (Blueprint,
                   render_template,
                   request,
                   redirect,
                   abort,
                   flash,
                   url_for,
                   current_app as app)


from roosterapp.templates.messages import *
from roosterapp.sql import *

dole_crud = Blueprint('dole_crud', __name__, template_folder='templates', url_prefix='/doles')

@dole_crud.route('/', methods=['GET'])
def show_doles():
    doles = app.db.session.query(Dole).all()
    return render_template('index_doles.html', doles = doles)

@dole_crud.route('/update/<id>', methods=['GET'])
def show_update_dole(id):
    if dole := app.db.session.query(Dole).get(id):
        return render_template('update_dole.html', dole=dole)
    else:
        return redirect(url_for('dole_crud.show_doles'))

@dole_crud.route('/add', methods=['POST'])
def create_dole():
    name = request.form.get('dole_name', '')
    dole = Dole(name=name)
    app.db.session.add(dole)
    app.db.session.commit()
    return redirect(url_for('dole_crud.show_doles'))

@dole_crud.route('/delete/<id>')
def delete_dole(id):
    if dole := app.db.session.query(Dole).get(id):
        app.db.session.delete(dole)
        app.db.session.commit()
    return redirect(url_for('dole_crud.show_doles'))

@dole_crud.route('/update/<id>', methods=['POST'])
def update_dole(id=None):
    if not (dole := app.db.session.query(Dole).get(id)):
        flash("Dagdeel bestaat niet")
        return redirect(url_for('dole_crud.show_doles'))
    name = request.form.get('dole_name', '')
    dole.name = name
    app.db.session.commit()
    return redirect(url_for('dole_crud.show_doles'))



profile_crud = Blueprint('profile_crud', __name__, template_folder='templates', url_prefix='/profiles')

@profile_crud.route('/', methods=['GET'])
def show_profiles():
    profiles = app.db.session.query(Profile).all()
    return render_template('index_profiles.html', profiles = profiles)

@profile_crud.route('/update/<id>', methods=['GET'])
def show_update_profile(id):
    if profile := app.db.session.query(Profile).get(id):
        return render_template('update_profile.html', profile=profile)
    else:
        return redirect(url_for('profile_crud.show_profiles'))

@profile_crud.route('/add', methods=['POST'])
def create_profile():
    name = request.form.get('profile_name', '')
    try:
        ratio = int(request.form.get('profile_ratio', '1'))
    except ValueError:
        flash("Ongeldig getal ingevoerd")
        return redirect(url_for('profile_crud.show_profiles'))
    profile = Profile(name=name, ratio=ratio)
    app.db.session.add(profile)
    app.db.session.commit()
    return redirect(url_for('profile_crud.show_profiles'))

@profile_crud.route('/delete/<id>')
def delete_profile(id):
    if profile := app.db.session.query(Profile).get(id):
        app.db.session.delete(profile)
        app.db.session.commit()
    return redirect(url_for('profile_crud.show_profiles'))

@profile_crud.route('/update/<id>', methods=['POST'])
def update_dole(id=None):
    if not (profile := app.db.session.query(Profile).get(id)):
        flash("Profiel bestaat niet")
        return redirect(url_for('profile_crud.show_profiles'))
    name = request.form.get('profile_name', '')
    try:
        ratio = int(request.form.get('profile_ratio', '1'))
    except ValueError:
        flash("Ongeldig getal ingevoerd")
        return redirect(url_for('profile_crud.show_profiles'))
    profile.name = name
    profile.ratio = ratio
    app.db.session.commit()
    return redirect(url_for('profile_crud.show_profiles'))