from mip import *
from enum import Enum


class Dole(Enum):
    MaO = 0
    MaM = 1
    DiO = 2
    DiM = 3
    WoO = 4
    WoM = 5
    DoO = 6
    DoM = 7
    VrO = 8
    VrM = 9

d=0
doleHours = {}
for data in Dole:
    d += 1
    doleHours[data.name] = 4

m = Model()


zz = {1: 1/6, 2: 1/3, 3: 1}


class person():
    def __init__(this, name, present = [], absent = []):
        this.name = name
        this.present = present
        this.absent = absent

    def printDole(this, d, v):
        if d in map(lambda dole : dole.value, this.present):
            return 'V'
        if d in map(lambda dole : dole.value, this.absent):
            return 'X'
        return str(v)


class client(person):
    def __init__(this, name, zz, dd, present = [], absent = []):
        super().__init__(name, present, absent)
        this.zz = zz
        this.dd = dd*4


class staff(person):
    def __init__(this, name, present = [], absent = [], lower = 0, upper = 10):
        super().__init__(name, present, absent)
        this.lower = lower
        this.upper = upper

class session():
    def __init__(this, client, staff, hours):
        this.client = client
        this.staff = staff
        this.hours = hours

staffs = [
          staff("A", [Dole.MaO], [Dole.VrO, Dole.VrM]),
          staff("B", [Dole.DiO, Dole.DiM], [Dole.DoO, Dole.DoM]),
          staff("C", [Dole.WoM]),
          staff("D", [Dole.VrO, Dole.VrM], [Dole.MaO, Dole.MaM]),
          staff("E"),
          staff("F"),
          staff("G"),
          staff("H"),
          staff("I"),
          staff("J"),
          staff("K")
         ]
s = len(staffs)


clients = [
        client("N.W.", 1, 9),
        client("C.M.", 1, 9),
        client("D.L.J.", 1, 4),
        client("M. de V.", 2, 9, absent=[Dole.WoM]),
        client("B. van B.", 2, 9, absent=[Dole.WoM]),
        client("A.F.", 2, 9, absent=[Dole.WoM]),
        client("F.H.", 3, 3),
        client("I.B.", 3, 6),
        client("E.H.", 3, 5),
        client("B.v.D.", 3, 4),
        client("J.V.", 3, 4),
        client("M.Z.", 3, 4, absent=[Dole.WoM]),
        client("P. van G.", 3, 4, absent=[Dole.MaO, Dole.DiO, Dole.WoO, Dole.DoO, Dole.VrO]),
        client("J. van der V.", 3, 4),
        client("K.C.", 3, 2),
        client("T.H.", 2, 5)
    ]
k = len(clients)


sessions = [
    # session(0, 1, 2),
    # session(0, 1, 2),
    # session(5, 4, 3),
    session(8, 4, 1)
]
b = len(sessions)

totalDoles = 0
for i in range(k):
    totalDoles += clients[i].dd * zz[clients[i].zz]
print(totalDoles)

ddClients       = [[m.add_var(name=f"x_{i}_{j}", var_type=BINARY) for j in range(10)] for i in range(k)]

ddStaffs     = [[m.add_var(name=f"s_{i}_{j}", var_type=BINARY) for j in range(10)] for i in range(s)]

ddSessions   = [[m.add_var(name=f"b_{i}_{j}", var_type=BINARY) for j in range(10)] for i in range(b)]

slackVars    = [m.add_var(name=f"e_{j}", var_type=CONTINUOUS) for j in range(10)]

# Every kid is scheduled for the right number of doles
for i in range(k):
    m += xsum(ddClients[i]*4) == clients[i].dd
    for dole in clients[i].present:
        m += ddClients[i][dole.value] == 1
    for dole in clients[i].absent:
        m += ddClients[i][dole.value] == 0


# Set staffing vars based on present/absent input
for i in range(s):
    m += xsum(ddStaffs[i]) <= staffs[i].upper
    m += xsum(ddStaffs[i]) >= staffs[i].lower
    for dole in staffs[i].present:
        m += ddStaffs[i][dole.value] == 1
    for dole in staffs[i].absent:
        m += ddStaffs[i][dole.value] + 1 == 1

# A session's client is scheduled, its staff isn't
for i in range(b):
    m += xsum(ddSessions[i][j] for j in range(10)) == 1
    for dole in Dole:
        j = dole.value
        m+= ddSessions[i][j] + ddClients[sessions[i].client][j] <= 1
        m+= ddSessions[i][j] <= ddStaffs[sessions[i].staff][j]

# Per dole the sum of adjusted kid-hours plus slack equals the staffing
for dole in Dole:
    j = dole.value
    m += xsum(zz[clients[i].zz] * ddClients[i][j] for i in range(k)) + slackVars[j] == xsum(ddStaffs[i][j] for i in range(s))

m.objective = minimize(xsum(slackVars[j] for j in range(10)))

m.optimize()

# Formatting

maxName = max([len(clients[i].name) for i in range(k)])
header = f"{' ' * maxName}  zz || MaO|MaM || DiO|DiM || WoO|WoM || DoO|DoM || VrO|VrM"
print(header)
print('=' * len(header))

for i in range(k):
    name = f"{clients[i].name}{' ' * (maxName - len(clients[i].name))} | {clients[i].zz} ||  "
    days = [f"{clients[i].printDole(2*j, ddClients[i][2*j].x)} | {clients[i].printDole(2*j+1, ddClients[i][2*j+1].x)}" for j in range(5)]
    row = "  ||  ".join(days)
    print(name+row)

print('=' * len(header))

# Totals per dole

doles = [sum(ddStaffs[i][dole.value].x for i in range(s)) for dole in Dole]
total = f"Totaal: {sum(doles)}"
total = total + f"{' ' * (maxName - len(total))}     ||  "
days = [f"{doles[2*j]}{' ' * (2 - len(str(doles[2*j])))}|{' ' * (2 - len(str(doles[2*j + 1])))}{doles[2*j + 1]}" for j in range(5)]
row = "  ||  ".join(map(str, days))
print(total+row)

print('=' * len(header))

# Total staffing hours 
for i in range(s):
    name = f"{staffs[i].name}{' ' * (maxName - len(staffs[i].name))}     ||  "
    days = [f"{staffs[i].printDole(2*j, ddStaffs[i][2*j].x)} | {staffs[i].printDole(2*j+1, ddStaffs[i][2*j+1].x)}" for j in range(5)]
    row = "  ||  ".join(days)
    print(name+row)

# for v in m.vars:
#     print(f"{v.name}: {v.x}")

# for constr in m.constrs:
#     print(constr)
