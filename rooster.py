from mip import *

m = Model()


zz = {1: 1/6, 2: 1/3, 3: 1}

class kid():
	def __init__(this, name, zz, dd):
		this.name = name
		this.zz = zz
		this.dd = dd

kids = [
		kid("N.W.", 1, 9),
		kid("C.M.", 1, 9),
		kid("D.L.J.", 1, 4),
		kid("M. de V.", 2, 9),
		kid("B. van B.", 2, 9),
		kid("A.F.", 2, 9),
		kid("F.H.", 3, 3),
		kid("I.B.", 3, 6),
		kid("E.H.", 3, 5),
		kid("B.v.D.", 3, 4),
		kid("J.V.", 3, 4),
		kid("M.Z.", 3, 4),
		kid("P. van G.", 3, 4),
		kid("J. van der V.", 3, 4),
		kid("K.C.", 3, 2)
	   ]
k = len(kids)

ddVars = [[m.add_var(name=f"x_{i}_{j}", var_type=BINARY) for j in range(10)] for i in range(k)]

slackVars = [m.add_var(name=f"s_{j}", var_type=CONTINUOUS) for j in range(10)]

staffingVars = [m.add_var(name=f"d_{j}", var_type=INTEGER) for j in range(10)]

for i in range(k):
	m += xsum(ddVars[i]) == kids[i].dd

for j in range(10):
	m += xsum(zz[kids[i].zz] * ddVars[i][j] for i in range(k)) + slackVars[j] == staffingVars[j]

m.objective = minimize(xsum(slackVars[j] for j in range(10)))

m.optimize()

# Formatting

maxName = max([len(kids[i].name) for i in range(k)])
header = f"{' ' * maxName}  zz || MaO|MaM || DiO|DiM || WoO|WoM || DoO|DoM || VrO|VrM"
print(header)
print('=' * len(header))

for i in range(k):
	name = f"{kids[i].name}{' ' * (maxName - len(kids[i].name))} | {kids[i].zz} ||  "
	days = [f"{ddVars[i][j].x} | {ddVars[i][j+1].x}" for j in range(5)]
	row = "  ||  ".join(days)
	print(name+row)

print('=' * len(header))
staffDays = [f"{staffingVars[j].x} | {staffingVars[j+1].x}" for j in range(5)]
lastRow = "  ||  ".join(staffDays)
total = f"Totaal: {sum([staffingVars[j].x for j in range(10)])}"
total = total + f"{' ' * (4 + maxName - len(total))} ||  "
print(total + lastRow)


# for v in m.vars:
# 	print(f"{v.name}: {v.x}")