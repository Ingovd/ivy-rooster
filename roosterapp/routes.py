from collections import defaultdict
from typing import Callable, Optional
from mip import *


from flask import (Blueprint,
                   render_template,
                   request,
                   session,
                   redirect,
                   abort,
                   flash,
                   url_for,
                   current_app as app)

from roosterapp.templates.messages import *
from roosterapp.sql import *


def generate(doles, clients, staffs, sessions):
    m = Model()
    doleSlackVars = defaultdict(dict)
    clientSlackVars = defaultdict(dict)
    clientGroup = defaultdict(dict)
    clientPresent = defaultdict(dict)
    staffGroup = defaultdict(dict)
    staffPresent = defaultdict(dict)
    sessionVars = defaultdict(dict)

    # Constants based on input
    # Number of hours each staff member is assigned
    staffSessionHours = defaultdict(lambda: 0)
    for session in sessions:
        staffSessionHours[session.staff.person_id] += session.hours

    # All scheduling booleans for clients/staff/sessions
    for dole in doles:
        j = dole.id
        for client in clients:
            i = client.person.id
            clientGroup[i][j] = m.add_var(name=f"k_{i}_{j}", var_type=BINARY)
            clientPresent[i][j] = m.add_var(name=f"cpresent_{i}_{j}", var_type=BINARY)
            # Group attendance implies presence
            m += clientGroup[i][j] <= clientPresent[i][j]
        for staff in staffs:
            i = staff.person.id
            staffGroup[i][j] = m.add_var(name=f"s_{i}_{j}", var_type=BINARY)
            staffPresent[i][j] = m.add_var(name=f"spresent_{i}_{j}", var_type=BINARY)
            # Group duty implies presence
            m += staffGroup[i][j] <= staffPresent[i][j]
        for session in sessions:
            i = session.id
            sessionVars[i][j] = m.add_var(name=f"b_{i}_{j}", var_type=BINARY)

    # Slack vars for objective function
    for client in clients:
        i = client.person.id
        clientSlackVars[i] = m.add_var(name=f"e_{i}", var_type=CONTINUOUS)
    for dole in doles:
        j = dole.id
        doleSlackVars[j] = m.add_var(name=f"d_{j}", var_type=CONTINUOUS)

    # print(doleSlackVars, flush=True)
    # print(clientVars, flush=True)
    # print(staffVars, flush=True)
    # print(sessionVars, flush=True)

    # Every kid is scheduled for the right number of doles
    for client in clients:
        i = client.person.id
        m += 0 <= clientSlackVars[i]
        m += client.hours + clientSlackVars[i] == xsum(clientGroup[i][dole.id] * dole.hours for dole in doles)
        for a in client.person.atttendance:
            if a.present == 0:
                m += clientPresent[i][a.dole.id] == 0
            elif a.present == 1:
                m += clientGroup[i][a.dole.id] == 1
            else:
                m += clientGroup[i][a.dole.id] == 0
        clientSessionVars = []
        for session in sessions:
            if session.client.person.id == client.person.id:
                clientSessionVars.append(session)
        for dole in doles:
            m += xsum(session.hours*sessionVars[session.id][dole.id] for session in clientSessionVars) <= dole.hours


    # Set staffing vars based on present/absent input
    for staff in staffs:
        i = staff.person.id
        m += staff.min_hours <= xsum(dole.hours * staffGroup[i][dole.id] for dole in doles)
        m += xsum(dole.hours * staffGroup[i][dole.id] for dole in doles) <= staff.max_hours

        for a in staff.person.atttendance:
            if a.present == 0:
                m += staffPresent[i][a.dole.id] == 0
            elif a.present == 1:
                m += staffGroup[i][a.dole.id] == 1
            else:
                m += staffGroup[i][a.dole.id] == 0
        staffSessionVars = []
        for session in sessions:
            if session.staff.person.id == staff.person.id:
                staffSessionVars.append(session)
        for dole in doles:
            m += xsum(session.hours*sessionVars[session.id][dole.id] for session in staffSessionVars) <= dole.hours


    # A session's client is scheduled, its staff isn't
    for session in sessions:
        i = session.id
        # Every session is scheduled on exactly one dole
        m += xsum(sessionVars[i][dole.id] for dole in doles) == 1
        for dole in doles:
            j = dole.id
            # Session can only be scheduled if staff and client are present
            m+= sessionVars[i][j] <= staffPresent[session.staff.person.id][j]
            m+= sessionVars[i][j] <= clientPresent[session.client.person.id][j]
            # Session can only be scheduled if staff is not scheduled for group
            m+= sessionVars[i][j] + staffGroup[session.staff.person.id][j] <= 1 

    # Per dole the sum of adjusted kid-hours plus slack equals the staffing
    for dole in doles:
        j = dole.id
        m += xsum(clientGroup[client.person.id][j] / client.profile.ratio
                    for client in clients) + doleSlackVars[j] == xsum(staffGroup[staff.person.id][j] for staff in staffs)

    m.objective = minimize(
        (xsum(doleSlackVars[dole.id] for dole in doles)
        + xsum(clientSlackVars[client.person.id] / client.profile.ratio for client in clients)) * 10000
        + xsum(clientPresent[client.person.id][dole.id] for dole in doles for client in clients))
    m.optimize()

    boolify_vars(clientGroup)
    boolify_vars(staffGroup)
    boolify_vars(sessionVars)

    return clientGroup, staffGroup, sessionVars

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
    personHours = defaultdict(lambda: 0)
    for session in sessions:
        personHours[session.staff.person_id] += session.hours
    for dole in doles:
        for session in sessions:
            if sessionRooster[session.id][dole.id]:
                personSessions[session.client.person.id][dole.id].append(session)
                personSessions[session.staff.person.id][dole.id].append(session)
        for client in clients:
            if clientRooster[client.person_id][dole.id]:
                personHours[client.person_id] += dole.hours
        for staff in staffs:
            if staffRooster[staff.person_id][dole.id]:
                personHours[staff.person_id] += dole.hours


    return render_template('complete_rooster.html',
        clientRooster=clientRooster, staffRooster=staffRooster, personSessions=personSessions,
        personHours=personHours, doles=doles, clients=clients, staffs=staffs, sessions=sessions)
    

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
    week_hours = sum(dole.hours for dole in doles)

    client_ids = [client.person_id for client in clients]
    staff_ids = [staff.person_id for staff in staffs]
    persons = [client.person for client in clients] + [staff.person for staff in staffs]
    for person in persons:
        person.present_sum = 0
        person.absent_sum = 0

    presences = app.db.session.query(Presence).filter(Presence.person_id.in_([person.id for person in persons]))
    for presence in presences:
        rooster[presence.person_id][presence.dole_id] = presence.present
        if presence.present:
            presence.person.present_sum += presence.dole.hours
        else:
            presence.person.absent_sum += presence.dole.hours
    
    session['rooster'] = rooster

    return render_template('rooster.html', week_hours=week_hours, staffs=staffs, clients=clients, doles=doles, rooster=rooster)


@rooster_maker.route('/presence/update', methods=['POST'])
def update_rooster():
    clients = app.db.session.query(Client).join(Person).filter(Person.active)
    staffs = app.db.session.query(Staff).join(Person).filter(Person.active)
    doles = app.db.session.query(Dole).all()

    client_ids = [client.person_id for client in clients]
    staff_ids = [staff.person_id for staff in staffs]
    person_ids = client_ids + staff_ids

    # app.db.session.query(Presence).delete()
    # app.db.session.commit()

    rooster = session.get('rooster', {});

    for person_id in person_ids:
        for dole in doles:
            form_id = f"{person_id}_{dole.id}"
            if f"presence_{form_id}" not in request.form:
                # Check of the old rooster had a presence
                if str(dole.id) in rooster.get(str(person_id), {}):
                    # Delete it if it exists
                    app.db.session.query(Presence).filter(Presence.person_id == person_id, Presence.dole_id == dole.id).delete()
            elif form_id in request.form:
                present = int(request.form[form_id])
                if dole.id not in rooster.get(person_id, {}) or rooster[person_id][dole.id] != present:
                    if presence := app.db.session.query(Presence).filter(Presence.person_id == person_id, Presence.dole_id == dole.id).first():
                        presence.present = present
                    else:
                        presence = Presence(person_id=person_id, dole_id=dole.id, present=present)
                        app.db.session.add(presence)

    try:
        app.db.session.commit()
    except:
        flash("Er ging iets fout bij het opslaan van de informatie")
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
    client_id = request.form.get('client_id', '')
    staff_id = request.form.get('staff_id', '')
    try:
        hours = float(request.form.get('hours', '1'))
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
        hours = float(request.form.get('hours', '1'))
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
        hours = float(request.form.get('hours', '1'))
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
        hours = float(request.form.get('hours', '1'))
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
        min_hours = float(request.form.get('min_hours', '1'))
        max_hours = float(request.form.get('max_hours', '1'))
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
        hours = float(request.form.get('hours', '1'))
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
        hours = float(request.form.get('hours', '1'))
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
        ratio = float(request.form.get('profile_ratio', '1'))
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
        ratio = float(request.form.get('profile_ratio', '1'))
    except ValueError:
        flash("Ongeldig getal ingevoerd")
        return redirect(url_for('profile_crud.show_profiles'))
    profile.name = name
    profile.ratio = ratio
    app.db.session.commit()
    return redirect(url_for('profile_crud.show_profiles'))