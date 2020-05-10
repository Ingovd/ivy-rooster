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

client_crud = Blueprint('client_crud', __name__, template_folder='templates', url_prefix='/clients')

@client_crud.route('/', methods=['GET'])
def show_clients():
    clients = app.db.session.query(Client).all()
    profiles = app.db.session.query(Profile).all()
    return render_template('index_clients.html', clients=clients, profiles=profiles)

@client_crud.route('/update/<id>', methods=['GET'])
def show_update_client(id):
    if client := app.db.session.query(Client).get(id):
        return render_template('update_client.html', client=client)
    else:
        return redirect(url_for('client_crud.show_clients'))

@client_crud.route('/add', methods=['POST'])
def create_client():
    print(request.form)
    name = request.form.get('client_name', '')
    profile_id = request.form.get('profile_id','')
    person = Person(name=name)
    app.db.session.add(person)
    app.db.session.commit()
    client = Client(person_id = person.id, profile_id = profile_id)
    app.db.session.add(client)
    app.db.session.commit()
    return redirect(url_for('client_crud.show_clients'))

@client_crud.route('/delete/<id>')
def delete_client(id):
    if client := app.db.session.query(Client).get(id):
        person = client.person
        app.db.session.delete(client)
        app.db.session.delete(person)
        app.db.session.commit()
    return redirect(url_for('client_crud.show_clients'))

@client_crud.route('/update/<id>', methods=['POST'])
def update_client(id=None):
    if not (client := app.db.session.query(Client).get(id)):
        flash("Client bestaat niet")
        return redirect(url_for('client_crud.show_clients'))
    name = request.form.get('client_name', '')
    profile_id = request.form.get('profile_id', '')
    client.person.name = name
    client.profile_id = profile_id
    app.db.session.commit()
    return redirect(url_for('client_crud.show_clients'))

staff_crud = Blueprint('staff_crud', __name__, template_folder='templates', url_prefix='/staffs')

@staff_crud.route('/', methods=['GET'])
def show_staffs():
    staffs = app.db.session.query(Staff).all()
    return render_template('index_staffs.html', staffs = staffs)

@staff_crud.route('/update/<id>', methods=['GET'])
def show_update_staff(id):
    if staff := app.db.session.query(Staff).get(id):
        return render_template('update_staff.html', staff=staff)
    else:
        return redirect(url_for('staff_crud.show_staffs'))

@staff_crud.route('/add', methods=['POST'])
def create_staff():
    name = request.form.get('staff_name', '')
    person = Person(name=name)
    app.db.session.add(person)
    app.db.session.commit()
    staff = Staff(person_id = person.id)
    app.db.session.add(staff)
    app.db.session.commit()
    return redirect(url_for('staff_crud.show_staffs'))

@staff_crud.route('/delete/<id>')
def delete_staff(id):
    if staff := app.db.session.query(Staff).get(id):
        person = staff.person
        app.db.session.delete(staff)
        app.db.session.delete(person)
        app.db.session.commit()
    return redirect(url_for('staff_crud.show_staffs'))

@staff_crud.route('/update/<id>', methods=['POST'])
def update_staff(id=None):
    if not (staff := app.db.session.query(Staff).get(id)):
        flash("Medewerker bestaat niet")
        return redirect(url_for('staff_crud.show_staffs'))
    name = request.form.get('staff_name', '')
    staff.person.name = name
    app.db.session.commit()
    return redirect(url_for('staff_crud.show_staffs'))

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