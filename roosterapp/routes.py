from collections import defaultdict
from typing import Callable, Optional
from mip import *


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


def generate(doles, clients, staffs, sessions):
    m = Model()
    slackVars = defaultdict(dict)
    clientVars = defaultdict(dict)
    staffVars = defaultdict(dict)
    sessionVars = defaultdict(dict)

    # All scheduling booleans for clients/staff/sessions
    for dole in doles:
        j = dole.id
        slackVars[j] = m.add_var(name=f"d_{j}", var_type=CONTINUOUS)
        for client in clients:
            i = client.person.id
            clientVars[i][j] = m.add_var(name=f"k_{i}_{j}", var_type=BINARY)
        for staff in staffs:
            i = staff.person.id
            staffVars[i][j] = m.add_var(name=f"s_{i}_{j}", var_type=BINARY)
        for session in sessions:
            i = session.id
            sessionVars[i][j] = m.add_var(name=f"b_{i}_{j}", var_type=BINARY)

    print(slackVars, flush=True)
    print(clientVars, flush=True)
    print(staffVars, flush=True)
    print(sessionVars, flush=True)

    # Every kid is scheduled for the right number of doles
    for client in clients:
        i = client.person.id
        m += client.hours <= xsum(clientVars[i][dole.id] * dole.hours for dole in doles)
        for a in client.person.atttendance:
            if a.present:
                m += clientVars[i][a.dole.id] == 1
            else:
                m += clientVars[i][a.dole.id] == 0
        clientSessionVars = []
        for session in sessions:
            if session.client.person.id == client.person.id:
                clientSessionVars.append(session)
        for dole in doles:
            m += xsum(session.hours*sessionVars[session.id][dole.id] for session in clientSessionVars) <= dole.hours


    # Set staffing vars based on present/absent input
    for staff in staffs:
        i = staff.person.id
        for a in staff.person.atttendance:
            if a.present:
                m += staffVars[i][a.dole.id] == 1
            else:
                m += staffVars[i][a.dole.id] == 0
        staffSessionVars = []
        for session in sessions:
            if session.staff.person.id == staff.person.id:
                staffSessionVars.append(session)
        for dole in doles:
            m += xsum(session.hours*sessionVars[session.id][dole.id] for session in staffSessionVars) <= dole.hours


    # A session's client is scheduled, its staff isn't
    for session in sessions:
        i = session.id
        m += xsum(sessionVars[i][dole.id] for dole in doles) == 1
        for dole in doles:
            j = dole.id
            # For b = sessionVars[i][j]
            #     x = clientVars[session.client.person.id][j]
            #     s = staffVars[session.staff.person.id][j]
            # encode: b -> x & !s
            m+= sessionVars[i][j] + staffVars[session.staff.person.id][j] <= 1
            m+= sessionVars[i][j] <= clientVars[session.client.person.id][j]

    # Per dole the sum of adjusted kid-hours plus slack equals the staffing
    for dole in doles:
        j = dole.id
        m += xsum(clientVars[client.person.id][j] / client.profile.ratio
                    for client in clients) + slackVars[j] == xsum(staffVars[staff.person.id][j] for staff in staffs)

    m.objective = minimize(xsum(slackVars[dole.id] for dole in doles))
    m.optimize()

    boolify_vars(clientVars)
    boolify_vars(staffVars)
    boolify_vars(sessionVars)

    return clientVars, staffVars, sessionVars

def boolify_vars(rooster):
    for item, doles in rooster.items():
        for dole, var in doles.items():
            print(var, flush=True)
            try:
                rooster[item][dole] = int(var.x) == 1
            except:
                rooster[item][dole] = False

rooster_maker = Blueprint('rooster_maker', __name__, template_folder='templates')

@rooster_maker.route('/rooster', methods=['POST'])
def generate_rooster():
    doles = app.db.session.query(Dole).all()
    clients = app.db.session.query(Client).join(Person).filter(Person.active)
    staffs = app.db.session.query(Staff).join(Person).filter(Person.active)
    clientSessions = {}
    for client in clients:
        for session in client.sessions:
            clientSessions[session.id] = session
    sessions = []
    for staff in staffs:
        for session in staff.sessions:
            if session.id in clientSessions:
                sessions.append(session)

    print("Generating roosters", flush=True)
    clientRooster, staffRooster, sessionRooster = generate(doles, clients, staffs, sessions)
    personSessions = defaultdict(lambda : defaultdict(list))
    for session in sessions:
        for dole in doles:
            if sessionRooster[session.id][dole.id]:
                personSessions[session.client.person.id][dole.id].append(session)
                personSessions[session.staff.person.id][dole.id].append(session)

    return render_template('complete_rooster.html',
        clientRooster=clientRooster, staffRooster=staffRooster, personSessions=personSessions,
        doles=doles, clients=clients, staffs=staffs, sessions=sessions)
    

@rooster_maker.route('/', methods=['GET'])
def show_rooster():
    rooster = {}
    clients = app.db.session.query(Client).join(Person).filter(Person.active)
    for client in clients:
        rooster[client.person.id] = {}
    staffs = app.db.session.query(Staff).join(Person).filter(Person.active)
    for staff in staffs:
        rooster[staff.person.id] = {}
    doles = app.db.session.query(Dole).all()

    client_ids = [client.person_id for client in clients]
    staff_ids = [staff.person_id for staff in staffs]
    person_ids = client_ids + staff_ids
    presences = app.db.session.query(Presence).filter(Presence.person_id.in_(person_ids))
    for presence in presences:
        rooster[presence.person_id][presence.dole_id] = presence.present
    
    return render_template('rooster.html', staffs=staffs, clients=clients, doles=doles, rooster=rooster)


@rooster_maker.route('/presence/update', methods=['POST'])
def update_rooster():
    clients = app.db.session.query(Client).join(Person).filter(Person.active)
    staffs = app.db.session.query(Staff).join(Person).filter(Person.active)
    doles = app.db.session.query(Dole).all()

    client_ids = [client.person_id for client in clients]
    staff_ids = [staff.person_id for staff in staffs]
    person_ids = client_ids + staff_ids

    app.db.session.query(Presence).delete()
    app.db.session.commit()

    for person_id in person_ids:
        for dole in doles:
            form_id = f"{person_id}_{dole.id}"
            if f"presence_{form_id}" not in request.form:
                continue
            if form_id in request.form:
                present = request.form[form_id] == "present"
                presence = Presence(person_id=person_id, dole_id=dole.id, present=present)
                app.db.session.add(presence)

    app.db.session.commit()
    return redirect(url_for('rooster_maker.show_rooster'))


person_switch = Blueprint('person_switch', __name__, template_folder='templates', url_prefix='/persons')


@person_switch.route('/', methods=['GET'])
def show_persons():
    clients = app.db.session.query(Client).all()
    staffs = app.db.session.query(Staff).all()
    return render_template('switch_persons.html', clients=clients, staffs=staffs)


@person_switch.route('/update', methods=['POST'])
def update_persons():
    persons = app.db.session.query(Person).all()
    for person in persons:
        if str(person.id) in request.form:
            person.active = True
        else:
            person.active = False
    app.db.session.commit()
    return redirect(url_for('person_switch.show_persons'))


session_crud = Blueprint('session_crud', __name__, template_folder='templates', url_prefix='/sessions')


@session_crud.route('/', methods=['GET'])
def show_sessions():
    sessions = app.db.session.query(Session).all()
    clients = app.db.session.query(Client).all()
    staffs = app.db.session.query(Staff).all()
    return render_template('index_sessions.html', sessions=sessions, clients=clients, staffs=staffs)


@session_crud.route('/update/<id>', methods=['GET'])
def show_update_session(id):
    if session := app.db.session.query(Session).get(id):
        clients = app.db.session.query(Client).all()
        staffs = app.db.session.query(Staff).all()
        return render_template('update_session.html', session=session, clients=clients, staffs=staffs)
    else:
        return redirect(url_for('session_crud.show_sessions'))


@session_crud.route('/add', methods=['POST'])
def create_session():
    print(request.form)
    client_id = request.form.get('client_id', '')
    staff_id = request.form.get('staff_id', '')
    try:
        hours = int(request.form.get('hours', '1'))
    except ValueError:
        flash("Ongeldig getal ingevoerd")
        return redirect(url_for('session_crud.show_sessions'))
    session = Session(client_id = client_id, staff_id=staff_id, hours=hours)
    app.db.session.add(session)
    app.db.session.commit()
    return redirect(url_for('session_crud.show_sessions'))


@session_crud.route('/delete/<id>')
def delete_session(id):
    if session := app.db.session.query(Session).get(id):
        app.db.session.delete(session)
        app.db.session.commit()
    return redirect(url_for('session_crud.show_sessions'))


@session_crud.route('/update/<id>', methods=['POST'])
def update_client(id=None):
    if not (session := app.db.session.query(Session).get(id)):
        flash("IB bestaat niet")
        return redirect(url_for('session_crud.show_sessions'))
    client_id = request.form.get('client_id', '')
    staff_id = request.form.get('staff_id', '')
    try:
        hours = int(request.form.get('hours', '1'))
    except ValueError:
        flash("Ongeldig getal ingevoerd")
        return redirect(url_for('session_crud.show_sessions'))
    session.client_id = client_id
    session.staff_id = staff_id
    session.hours = hours
    app.db.session.commit()
    return redirect(url_for('session_crud.show_sessions'))


client_crud = Blueprint('client_crud', __name__, template_folder='templates', url_prefix='/clients')


@client_crud.route('/', methods=['GET'])
def show_clients():
    clients = app.db.session.query(Client).all()
    profiles = app.db.session.query(Profile).all()
    return render_template('index_clients.html', clients=clients, profiles=profiles)


@client_crud.route('/update/<id>', methods=['GET'])
def show_update_client(id):
    if client := app.db.session.query(Client).get(id):
        profiles = app.db.session.query(Profile).all()
        return render_template('update_client.html', client=client, profiles=profiles)
    else:
        return redirect(url_for('client_crud.show_clients'))


@client_crud.route('/add', methods=['POST'])
def create_client():
    print(request.form)
    name = request.form.get('client_name', '')
    try:
        hours = int(request.form.get('hours', '1'))
    except ValueError:
        flash("Ongeldig getal ingevoerd")
        return redirect(url_for('client_crud.show_clients'))
    profile_id = request.form.get('profile_id','')
    person = Person(name=name)
    app.db.session.add(person)
    app.db.session.commit()
    client = Client(person_id = person.id, hours=hours, profile_id = profile_id)
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
    try:
        hours = int(request.form.get('hours', '1'))
    except ValueError:
        flash("Ongeldig getal ingevoerd")
        return redirect(url_for('client_crud.show_clients'))
    client.person.name = name
    client.profile_id = profile_id
    client.hours = hours
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
    try:
        min_hours = int(request.form.get('min_hours', '1'))
        max_hours = int(request.form.get('max_hours', '1'))
    except ValueError:
        flash("Ongeldig getal ingevoerd")
        return redirect(url_for('staff_crud.show_staffs'))
    person = Person(name=name)
    app.db.session.add(person)
    app.db.session.commit()
    staff = Staff(person_id = person.id, min_hours=min_hours, max_hours=max_hours)
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
    try:
        min_hours = int(request.form.get('min_hours', '1'))
        max_hours = int(request.form.get('max_hours', '1'))
    except ValueError:
        flash("Ongeldig getal ingevoerd")
        return redirect(url_for('staff_crud.show_staffs'))
    staff.person.name = name
    staff.min_hours = min_hours
    staff.max_hours = max_hours
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
    try:
        hours = int(request.form.get('hours', '1'))
    except ValueError:
        flash("Ongeldig getal ingevoerd")
        return redirect(url_for('dole_crud.show_doles'))
    dole = Dole(name=name, hours=hours)
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
    try:
        hours = int(request.form.get('hours', '1'))
    except ValueError:
        flash("Ongeldig getal ingevoerd")
        return redirect(url_for('dole_crud.show_doles'))
    dole.name = name
    dole.hours = hours
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
def update_profile(id=None):
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